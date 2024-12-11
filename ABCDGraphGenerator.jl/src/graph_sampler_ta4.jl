struct ABCDParams4
    w::Vector{Int}
    s::Vector{Int}
    clusters::Vector{Vector{Int64}}
    mcs::Vector{Int64}
    μ::Union{Float64, Nothing}
    ξ::Union{Float64, Nothing}
    isCL::Bool
    islocal::Bool
    hasoutliers::Bool

    function ABCDParams4(w, s, clusters, mcs, μ, ξ, isCL, islocal, hasoutliers=false)
        length(w) == sum(s) || throw(ArgumentError("inconsistent data"))
        if !isnothing(μ)
            0 ≤ μ ≤ 1 || throw(ArgumentError("inconsistent data on μ"))
        end
        if !isnothing(ξ)
            0 ≤ ξ ≤ 1 || throw(ArgumentError("inconsistent data ξ"))
            if islocal
                throw(ArgumentError("when ξ is provided local model is not allowed"))
            end
        end
        if isnothing(μ) && isnothing(ξ)
            throw(ArgumentError("inconsistent data: either μ or ξ must be provided"))
        end

        if !(isnothing(μ) || isnothing(ξ))
            throw(ArgumentError("inconsistent data: only μ or ξ may be provided"))
        end

        if hasoutliers
            news = copy(s)
            sort!(@view(news[2:end]), rev=true)
        else
            p = sortperm(s, rev=true)
            news = copy(s[p])
            # mcs .= mcs[p]
            
            # TODO: Handle renaming clusters after sorting
            # Currently assuming cluster size is correctly sorted
            @assert news == s
        end

        p = sortperm(w, rev=true)
        neww = copy(w[p])
        clusters .= clusters[p]

        # TODO: Remove
        # This is only to make sure that w is sorted
        @assert neww == w

        new(neww,
            news,
            clusters,
            mcs,
            μ, ξ, isCL, islocal, hasoutliers)
    end
end

function config_model_ta4(clusters, params)
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

    connected_edges = Set{Tuple{Int, Int}}()
    edges = Set{Tuple{Int, Int}}()

    unresolved_collisions = 0
    w_internal = zeros(Int, length(w_internal_raw))
    for (cluster_id, cluster) in enumerate(clusterlist)
        maxw_idx = argmax(view(w_internal_raw, cluster))
        wsum = 0
        for i in axes(cluster, 1)
            if i != maxw_idx
                neww = randround(w_internal_raw[cluster[i]])
                # ============================================== S
                w_internal[cluster[i]] = neww
                wsum += neww
                # ============================================== O
                # w_internal[cluster[i]] = max(neww, 2)
                # wsum += w_internal[cluster[i]]
                # ============================================== E
            end
        end
        # ============================================== S
        maxw = floor(Int, w_internal_raw[cluster[maxw_idx]])
        # ============================================== O
        # maxw = max(floor(Int, w_internal_raw[cluster[maxw_idx]]), 2)
        # ============================================== E
        w_internal[cluster[maxw_idx]] = maxw + (isodd(wsum) ? iseven(maxw) : isodd(maxw))
        if w_internal[cluster[maxw_idx]] > w[cluster[maxw_idx]]
            @assert w[cluster[maxw_idx]] + 1 == w_internal[cluster[maxw_idx]]
            w[cluster[maxw_idx]] += 1
        end

        # ============================================== S
        # ABCD-TA-p-Con: Attempt 2

        # required = 2 * (length(cluster) - 1)
        # additional = required - wsum
        # while additional > 0
        #     not_found = true
        #     for i in cluster[sortperm(w_internal[cluster])]
        #         if w_internal[i] >= 2 || w_internal[i] == w[i]
        #             continue
        #         end
        #         not_found = false
        #         w_internal[i] += 1
        #         additional -= 1
        #         if additional == 0
        #             break
        #         end
        #     end

        #     if not_found
        #         for i in cluster[sortperm(w_internal[cluster])]
        #             if w_internal[i] >= 2
        #                 continue
        #             end
        #             w_internal[i] += 1
        #             w[i] += 1
        #             additional -= 1
        #             if additional == 0
        #                 break
        #             end
        #         end
        #     end
        # end

        # wsum = sum(w_internal[cluster])
        # maxw_idx = argmax(view(w_internal, cluster))
        # w_internal[cluster[maxw_idx]] += isodd(wsum) ? 1 : 0
        # if w_internal[cluster[maxw_idx]] > w[cluster[maxw_idx]]
        #     @assert w[cluster[maxw_idx]] + 1 == w_internal[cluster[maxw_idx]]
        #     w[cluster[maxw_idx]] += 1
        # end

        # ============================================== E

        w_internal_copy = copy(w_internal)

        if params.hasoutliers && cluster === clusterlist[1]
            @assert findall(clusters .== 1) == cluster
            @assert all(iszero, w_internal[cluster])
        end

        # ============================================== S
        # ABCD-TA-p-Con: Attempt 1

        # pool = Int[]
        # cluster_sorted = cluster[sortperm(w_internal[cluster], rev=true)]

        # for i in cluster_sorted
        #     if w_internal[i] == 0
        #         continue
        #     end

        #     if isempty(pool)
        #         push!(pool, i)
        #         continue
        #     end

        #     loc = pool[argmax(view(w_internal, pool))]

        #     if w_internal[loc] == 0
        #         continue
        #     end

        #     push!(local_edges, minmax(i, loc))
        #     w_internal[i] -= 1
        #     w_internal[loc] -= 1
        #     push!(pool, i)
        # end

        # wsum = sum(w_internal[cluster])
        # maxw_idx = argmax(view(w_internal, cluster))
        # w_internal[cluster[maxw_idx]] += isodd(wsum) ? 1 : 0
        # if w_internal[cluster[maxw_idx]] > w[cluster[maxw_idx]]
        #     @assert w[cluster[maxw_idx]] + 1 == w_internal[cluster[maxw_idx]]
        #     w[cluster[maxw_idx]] += 1
        # end

        # ============================================== E

        # ============================================== S
        # ABCD-TA-p-WellCon
        
        local_edges = Set{Tuple{Int, Int}}()
        pool = Int[]
        cluster_sorted = cluster[sortperm(w_internal[cluster], rev=true)]
        k = params.mcs[cluster_id]

        for i in cluster_sorted
            if k == 0
                break
            end
            
            if length(pool) < k
                for j in pool
                    if w_internal[j] == 0
                        if w_internal_copy[j] == w[j]
                            w[j] += 1
                        end
                        w_internal_copy[j] += 1
                        w_internal[j] += 1
                    end

                    if w_internal[i] == 0
                        if w_internal_copy[i] == w[i]
                            w[i] += 1
                        end
                        w_internal_copy[i] += 1
                        w_internal[i] += 1
                    end

                    push!(local_edges, minmax(i, j))
                    w_internal[i] -= 1
                    w_internal[j] -= 1
                end
                push!(pool, i)
                continue
            end

            t = 0
            if t == k
                break
            end
            selected = Set{Int}()

            # Find the top-k nodes with the highest available degree
            # and connect them to the current node
            for loc in pool[sortperm(view(w_internal, pool), rev=true)]
                if w_internal[loc] == 0
                    continue
                end

                if w_internal[i] == 0
                    if w_internal_copy[i] == w[i]
                        w[i] += 1
                    end
                    w_internal_copy[i] += 1
                    w_internal[i] += 1
                end

                push!(selected, loc)
                push!(local_edges, minmax(i, loc))
                w_internal[i] -= 1
                w_internal[loc] -= 1

                t += 1
                if t == k
                    break
                end
            end

            while t < k
                candidates = setdiff(pool, selected)
                wts = Weights(view(w_internal_copy, candidates))
                loc = sample(candidates, wts)

                if minmax(i, loc) in local_edges
                    continue
                end

                if w_internal[loc] == 0
                    if w_internal_copy[loc] == w[loc]
                        w[loc] += 1
                    end
                    w_internal_copy[loc] += 1
                    w_internal[loc] += 1
                end

                if w_internal[i] == 0
                    if w_internal_copy[i] == w[i]
                        w[i] += 1
                    end
                    w_internal_copy[i] += 1
                    w_internal[i] += 1
                end

                push!(selected, loc)
                push!(local_edges, minmax(i, loc))
                w_internal[i] -= 1
                w_internal[loc] -= 1

                t += 1
            end

            # if t < k
            #     for loc in pool[sortperm(view(w_internal_copy, pool), rev=true)]
            #         if w_internal[i] == 0
            #             break
            #         end

            #         if minmax(i, loc) in local_edges
            #             # println("Gotcha!")
            #             # readline()
            #             continue
            #         end

            #         if w_internal[loc] == 0
            #             if w_internal_copy[loc] == w[loc]
            #                 change += 1
            #                 w[loc] += 1
            #             end
            #             w_internal_copy[loc] += 1
            #             w_internal[loc] += 1
            #             # break
            #         end

            #         push!(local_edges, minmax(i, loc))
            #         w_internal[i] -= 1
            #         w_internal[loc] -= 1

            #         t += 1
            #         if t == k
            #             break
            #         end
            #     end
            # end

            # if change > 0
            #     println("Changes: ", change)
            # end

            # topk = partialsortperm(view(w_internal, pool), 1:k, rev=true)
            # locs = pool[topk]

            # for loc in locs
            #     if w_internal[loc] == 0
            #         continue
            #     end

            #     push!(local_edges, minmax(i, loc))
            #     w_internal[i] -= 1
            #     w_internal[loc] -= 1
            # end

            push!(pool, i)
        end

        wsum = sum(w_internal[cluster])
        maxw_idx = argmax(view(w_internal, cluster))
        w_internal[cluster[maxw_idx]] += isodd(wsum) ? 1 : 0
        if w_internal[cluster[maxw_idx]] > w[cluster[maxw_idx]]
            @assert w[cluster[maxw_idx]] + 1 == w_internal[cluster[maxw_idx]]
            w[cluster[maxw_idx]] += 1
        end

        connected_graph = copy(local_edges)

        # ============================================== E

        stubs = Int[]
        for i in cluster
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
        
        local_edges = Set{Tuple{Int, Int}}()
        recycle = Tuple{Int,Int}[]
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
            # ================================ S
            # if p1 in connected_graph
            #     continue
            # end
            # ================================ E
            from_recycle = 2 * length(recycle) / length(stubs)
            success = false
            for _ in 1:2:length(stubs)
                p2 = if rand() < from_recycle
                    used_recycle = true
                    recycle_idx = rand(axes(recycle, 1))
                    recycle[recycle_idx]
                else
                    if isempty(local_edges)
                        continue
                    end
                    used_recycle = false
                    rand(local_edges)
                end
                # ================================ S
                # c = 0
                # while p2 in connected_graph
                #     p2 = if rand() < from_recycle
                #         used_recycle = true
                #         recycle_idx = rand(axes(recycle, 1))
                #         recycle[recycle_idx]
                #     else
                #         candidates = setdiff(local_edges, connected_graph)
                #         if isempty(candidates)
                #             continue
                #         end
                #         used_recycle = false
                #         rand(candidates)
                #     end
                #     c += 1
                #     if c == 10
                #         break
                #     end
                # end
                # if p2 in connected_graph
                #     println("Failed to find a non-intrusive edge. Breaking...")
                #     continue
                # end
                # ================================ E
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

        # ============================================== S
        local_edges_copy = copy(local_edges)
        union!(local_edges, connected_graph)
        
        for u in cluster
            w_internal[u] = 0
        end
        for (u, v) in local_edges
            w_internal[u] += 1
            if w_internal[u] > w[u]
                @assert w[u] + 1 == w_internal[u]
                w[u] += 1
            end

            w_internal[v] += 1
            if w_internal[v] > w[v]
                @assert w[v] + 1 == w_internal[v]
                w[v] += 1
            end
        end
        local_edges = copy(local_edges_copy)
        connected_edges = union(connected_edges, connected_graph)
        # ============================================== E

        union!(edges, local_edges)
        
        # @assert length(edges) == old_len + length(local_edges)
        # @assert 2 * (length(local_edges) + length(recycle) - local_connected_edges_count) == length(stubs)
        for (a, b) in recycle
            w_internal[a] -= 1
            w_internal[b] -= 1
        end
        unresolved_collisions += length(recycle)
    end

    if unresolved_collisions > 0
        println("Unresolved_collisions: ", unresolved_collisions,
                "; fraction: ", 2 * unresolved_collisions / total_weight)
    end

    # ============================================== S
    # local_edges = copy(edges)
    # edges = Set{Tuple{Int, Int}}()
    # ============================================== E

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
            # ================================
            if isempty(global_edges)
                push!(recycle, p1)
                continue
            end
            # ================================
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

    # ============================================== S
    # union!(edges, local_edges)
    union!(edges, connected_edges)
    # ============================================== E

    return edges
end

function populate_clusters_ta4(params::ABCDParams4)
    clusters = fill(-1, length(params.w))
    for (v, c) in params.clusters
        clusters[v] = c
    end
    @assert minimum(clusters) == 1
    return clusters
end

function gen_graph_ta4(params::ABCDParams4)
    clusters = populate_clusters_ta4(params)
    edges = params.isCL ? CL_model(clusters, params) : config_model_ta4(clusters, params)
    (edges=edges, clusters=clusters)
end