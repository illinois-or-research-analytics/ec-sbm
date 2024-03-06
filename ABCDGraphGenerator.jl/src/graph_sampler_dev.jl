function populate_clusters_tadev(params::ABCDParams)
    w, s = params.w, params.s
    if isnothing(params.ξ)
        mul = 1.0 - params.μ
    else
        n = length(w)
        if params.hasoutliers
            s0 = s[1]
            n = length(params.w)
            ϕ = 1.0 - sum((sl/(n-s0))^2 for sl in s[2:end]) * (n-s0)*params.ξ / ((n-s0)*params.ξ + s0)
        else
            ϕ = 1.0 - sum((sl/n)^2 for sl in s)
        end
        mul = 1.0 - params.ξ*ϕ
    end
    @assert length(w) == sum(s)
    @assert 0 ≤ mul ≤ 1
    @assert issorted(w, rev=true)
    if params.hasoutliers
        @assert issorted(s[2:end], rev=true)
    else
        @assert issorted(s, rev=true)
    end

    slots = copy(s)
    clusters = fill(-1, length(w))

    if params.hasoutliers
        nout = s[1]
        n = length(params.w)
        L = sum(d -> min(1.0, params.ξ * d), params.w)
        threshold = L + nout - L * nout / n - 1.0
        idx = findfirst(<=(threshold), params.w)
        @assert all(i -> params.w[i] <= threshold, idx:n)
        if length(idx:n) < nout
            throw(ArgumentError("not enough nodes feasible for classification as outliers"))
        end
        tabu = sample(idx:n, nout, replace=false)
        clusters[tabu] .= 1
        slots[1] = 0
        stabu = Set(tabu)
    else
        stabu = Set{Int}()
    end

    j0 = params.hasoutliers ? 1 : 0
    j = j0
    for (i, vw) in enumerate(w)
        i in stabu && continue
        while j + 1 ≤ length(s) && mul * vw + 1 ≤ s[j + 1]
            j += 1
        end
        j == j0 && throw(ArgumentError("could not find a large enough cluster for vertex of weight $vw"))
        wts = Weights(view(slots, (j0+1):j))
        wts.sum == 0 && throw(ArgumentError("could not find an empty slot for vertex of weight $vw"))
        # loc = sample((j0+1):j, wts)

        # Count the number of non-zero in slots[j0+1:j]
        c = 0
        t = j0
        for k in (j0+1):j
            if slots[k] > 0
                c += 1
            end
        end
        
        ncandidates = c * 0.2

        # Only sample from the first 50% of the slots[j0+1:j] if there are more than 1 non-zero slots
        if ncandidates < 1
            # Find the first non-zero slot
            loc = j0 + 1
            while slots[loc] == 0
                loc += 1
            end
        else
            c = 0
            t = j0 + 1
            while t ≤ j && c < ncandidates
                if slots[t] > 0
                    c += 1
                end
                t += 1
            end
            wts = Weights(view(slots, (j0+1):t))
            loc = sample((j0+1):t, wts)
        end
        
        clusters[i] = loc
        slots[loc] -= 1
    end
    @assert sum(slots) == 0
    @assert minimum(clusters) == 1
    return clusters
end

function config_model_dev(clusters, params)
    @assert !params.isCL
    @assert !params.islocal
    w, s, μ = params.w, params.s, params.μ

    cluster_weight = zeros(Int, length(s))
    for i in axes(w, 1)
        cluster_weight[clusters[i]] += w[i]
    end
    total_weight = sum(cluster_weight)
    if params.islocal
        ξl = @. μ / (1.0 - cluster_weight / total_weight)
        maximum(ξl) >= 1 && throw(ArgumentError("μ is too large to generate a graph"))
        w_internal_raw = [w[i] * (1 - ξl[clusters[i]]) for i in axes(w, 1)]
    else
        if isnothing(params.ξ)
            @assert !params.hasoutliers
            ξg = μ / (1.0 - sum(x -> x^2, cluster_weight) / total_weight^2)
            ξg >= 1 && throw(ArgumentError("μ is too large to generate a graph"))
        else
            ξg = params.ξ
        end
        w_internal_raw = [w[i] * (1 - ξg) for i in axes(w, 1)]
        if params.hasoutliers
            for i in findall(==(1), clusters)
                w_internal_raw[i] = 0
            end
        end
    end

    clusterlist = [Int[] for i in axes(s, 1)]
    for i in axes(clusters, 1)
        push!(clusterlist[clusters[i]], i)
    end

    edges = Set{Tuple{Int, Int}}()

    unresolved_collisions = 0
    w_internal = zeros(Int, length(w_internal_raw))
    for cluster in clusterlist
        println("==========================================")
        println("Cluster: ", cluster)
        
        maxw_idx = argmax(view(w_internal_raw, cluster))
        wsum = 0
        for i in axes(cluster, 1)
            if i != maxw_idx
                neww = randround(w_internal_raw[cluster[i]])
                w_internal[cluster[i]] = neww
                wsum += w_internal[cluster[i]]
            end
        end
        maxw = floor(Int, w_internal_raw[cluster[maxw_idx]])
        w_internal[cluster[maxw_idx]] = maxw + (isodd(wsum) ? iseven(maxw) : isodd(maxw))
        if w_internal[cluster[maxw_idx]] > w[cluster[maxw_idx]]
            @assert w[cluster[maxw_idx]] + 1 == w_internal[cluster[maxw_idx]]
            w[cluster[maxw_idx]] += 1
        end
        wsum += w_internal[cluster[maxw_idx]]
        

        println("w_internal (before): ", w_internal[cluster])
        println("Missing: ", 2 * (length(cluster) - 1) - wsum)
        c = 0
        if wsum < 2 * (length(cluster) - 1)
            additional = 2 * (length(cluster) - 1) - wsum
            while additional > 0
                not_found = true
                for i in cluster[sortperm(w_internal[cluster])]
                    if w_internal[i] == w[i]
                        continue
                    end
                    not_found = false
                    w_internal[i] += 1
                    # w[i] += 1
                    additional -= 1
                    if additional == 0
                        break
                    end
                end

                if not_found
                    for i in cluster[sortperm(w_internal[cluster])]
                        w_internal[i] += 1
                        w[i] += 1
                        c += 1
                        additional -= 1
                        if additional == 0
                            break
                        end
                    end
                end
            end
        end
        println("Changes made: ", c)

        # println(w_internal_raw[cluster], w_internal[cluster])

        if params.hasoutliers && cluster === clusterlist[1]
            @assert findall(clusters .== 1) == cluster
            @assert all(iszero, w_internal[cluster])
        end

        # ===========================================
        # TODO: add edges here

        println("w_internal: ", w_internal[cluster])

        local_edges = Set{Tuple{Int, Int}}()
        recycle = Tuple{Int,Int}[]

        # pool = Int[]
        # cluster_sorted = cluster[sortperm(w_internal[cluster], rev=true)]
        # println("length(cluster_sorted): ", length(cluster_sorted))

        # for i in cluster_sorted
        #     if w_internal[i] == 0
        #         continue
        #     end

        #     if isempty(pool)
        #         push!(pool, i)
        #         continue
        #     end

        #     best = filter(e -> w_internal[e] == maximum(w_internal[pool]), pool)
        #     wts = Weights(view(w_internal, best))
        #     if wts.sum == 0
        #         continue
        #     end
        #     loc = sample(best, wts)
        #     push!(local_edges, minmax(i, loc))
        #     w_internal[i] -= 1
        #     w_internal[loc] -= 1
        #     push!(pool, i)
        # end

        pool = Int[]
        cluster_sorted = cluster[sortperm(w_internal[cluster], rev=true)]
        # println("length(cluster_sorted): ", length(cluster_sorted))

        for i in cluster_sorted
            if w_internal[i] == 0
                continue
            end

            if isempty(pool)
                push!(pool, i)
                continue
            end

            loc = pool[argmax(view(w_internal, pool))]

            if w_internal[loc] == 0
                continue
            end

            push!(local_edges, minmax(i, loc))
            w_internal[i] -= 1
            w_internal[loc] -= 1
            push!(pool, i)
        end

        println("Connected edges: ", local_edges)

        local_connected_edges_count = length(local_edges)

        # ===========================================

        stubs = Int[]
        for i in cluster[sortperm(w_internal[cluster])]
            for j in 1:w_internal[i]
                push!(stubs, i)
            end
        end
        @assert sum(w_internal[cluster]) == length(stubs)
        @assert iseven(length(stubs))

        if params.hasoutliers && cluster === clusterlist[1]
            @assert isempty(stubs)
        end
        
        shuffle!(stubs)

        for i in 1:2:length(stubs)
            e = minmax(stubs[i], stubs[i+1])
            if (e[1] == e[2]) || (e in local_edges)
                push!(recycle, e)
            else
                push!(local_edges, e)
            end
        end
        
        last_recycle = length(recycle)
        recycle_counter = last_recycle
        while !isempty(recycle)
            recycle_counter -= 1
            if recycle_counter < 0
                if length(recycle) < last_recycle
                    last_recycle = length(recycle)
                    recycle_counter = last_recycle
                else
                    break
                end
            end
            p1 = popfirst!(recycle)
            from_recycle = 2 * length(recycle) / length(stubs)
            success = false
            for _ in 1:2:length(stubs)
                p2 = if rand() < from_recycle
                    used_recycle = true
                    recycle_idx = rand(axes(recycle, 1))
                    recycle[recycle_idx]
                else
                    used_recycle = false
                    if isempty(local_edges)
                        continue
                    end
                    rand(local_edges)
                end

                if rand() < 0.5
                    newp1 = minmax(p1[1], p2[1])
                    newp2 = minmax(p1[2], p2[2])
                else
                    newp1 = minmax(p1[1], p2[2])
                    newp2 = minmax(p1[2], p2[1])
                end

                if newp1 == newp2
                    good_choice = false
                elseif (newp1[1] == newp1[2]) || (newp1 in local_edges)
                    good_choice = false
                elseif (newp2[1] == newp2[2]) || (newp2 in local_edges)
                    good_choice = false
                else
                    good_choice = true
                end

                if good_choice
                    if used_recycle
                        recycle[recycle_idx], recycle[end] = recycle[end], recycle[recycle_idx]
                        pop!(recycle)
                    else
                        pop!(local_edges, p2)
                    end
                    success = true
                    push!(local_edges, newp1)
                    push!(local_edges, newp2)
                    break
                end
            end
            success || push!(recycle, p1)
        end

        old_len = length(edges)
        union!(edges, local_edges)

        println("Edges: ", local_edges)
        println("Recycle: ", recycle)

        @assert length(edges) == old_len + length(local_edges)
        @assert 2 * (length(local_edges) + length(recycle) - local_connected_edges_count) == length(stubs)
        for (a, b) in recycle
            w_internal[a] -= 1
            w_internal[b] -= 1
        end
        unresolved_collisions += length(recycle)

        # println("Local edges: ", local_edges)
    end

    if unresolved_collisions > 0
        println("Unresolved_collisions: ", unresolved_collisions,
                "; fraction: ", 2 * unresolved_collisions / total_weight)
    end

    stubs = Int[]
    for i in axes(w, 1)
        for j in w_internal[i]+1:w[i]
            push!(stubs, i)
        end
    end
    @assert sum(w) == length(stubs) + sum(w_internal)
    if params.hasoutliers
        if 2 * sum(w[clusters .== 1]) > length(stubs)
            @warn "Because of low value of ξ the outlier nodes form a community. " *
                  "It is recommended to increase ξ."
        end
    end
    shuffle!(stubs)
    if isodd(length(stubs))
        maxi = 1
        @assert w[stubs[maxi]] > w_internal[stubs[maxi]]
        for i in 2:length(stubs)
            si = stubs[i]
            @assert w[si] > w_internal[si]
            if w[si] > w[stubs[maxi]]
                maxi = i
            end
        end
        si = popat!(stubs, maxi)
        @assert w[si] > w_internal[si]
        w[si] -= 1
    end
    global_edges = Set{Tuple{Int, Int}}()
    recycle = Tuple{Int,Int}[]
    for i in 1:2:length(stubs)
        e = minmax(stubs[i], stubs[i+1])
        if (e[1] == e[2]) || (e in global_edges) || (e in edges)
            push!(recycle, e)
        else
            push!(global_edges, e)
        end
    end
    last_recycle = length(recycle)
    recycle_counter = last_recycle
    while !isempty(recycle)
        recycle_counter -= 1
        if recycle_counter < 0
            if length(recycle) < last_recycle
                last_recycle = length(recycle)
                recycle_counter = last_recycle
            else
                break
            end
        end
        p1 = pop!(recycle)
        from_recycle = 2 * length(recycle) / length(stubs)
        p2 = if rand() < from_recycle
            i = rand(axes(recycle, 1))
            recycle[i], recycle[end] = recycle[end], recycle[i]
            pop!(recycle)
        else
            x = rand(global_edges)
            pop!(global_edges, x)
        end
        if rand() < 0.5
            newp1 = minmax(p1[1], p2[1])
            newp2 = minmax(p1[2], p2[2])
        else
            newp1 = minmax(p1[1], p2[2])
            newp2 = minmax(p1[2], p2[1])
        end
        for newp in (newp1, newp2)
            if (newp[1] == newp[2]) || (newp in global_edges) || (newp in edges)
                push!(recycle, newp)
            else
                push!(global_edges, newp)
            end
        end
    end
    old_len = length(edges)
    union!(edges, global_edges)
    @assert length(edges) == old_len + length(global_edges)
    if isempty(recycle)
        @assert 2 * length(global_edges) == length(stubs)
    else
        last_recycle = length(recycle)
        recycle_counter = last_recycle
        while !isempty(recycle)
            recycle_counter -= 1
            if recycle_counter < 0
                if length(recycle) < last_recycle
                    last_recycle = length(recycle)
                    recycle_counter = last_recycle
                else
                    break
                end
            end
            p1 = pop!(recycle)
            x = rand(edges)
            p2 = pop!(edges, x)
            if rand() < 0.5
                newp1 = minmax(p1[1], p2[1])
                newp2 = minmax(p1[2], p2[2])
            else
                newp1 = minmax(p1[1], p2[2])
                newp2 = minmax(p1[2], p2[1])
            end
            for newp in (newp1, newp2)
                if (newp[1] == newp[2]) || (newp in edges)
                    push!(recycle, newp)
                else
                    push!(edges, newp)
                end
            end
        end
    end
    if !isempty(recycle)
        unresolved_collisions = length(recycle)
        println("Very hard graph. Failed to generate ", unresolved_collisions,
                "edges; fraction: ", 2 * unresolved_collisions / total_weight)
    end
    return edges
end

"""
    gen_graph_tadev(params::ABCDParams)

Generate modified ABCD graph (dev) following parameters specified in `params`.

Return a named tuple containing a set of edges of the graph and a list of cluster
assignments of the vertices.
The ordering of vertices and clusters is in descending order (as in `params`).
"""
function gen_graph_tadev(params::ABCDParams)
    clusters = populate_clusters_tadev(params)
    edges = params.isCL ? CL_model(clusters, params) : config_model_dev(clusters, params)
    (edges=edges, clusters=clusters)
end