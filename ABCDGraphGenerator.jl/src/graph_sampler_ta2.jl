function populate_clusters_ta2(params::ABCDParams)
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
        
        ncandidates = c * 0.1

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

"""
    gen_graph_tadev(params::ABCDParams)

Generate modified ABCD graph (dev) following parameters specified in `params`.

Return a named tuple containing a set of edges of the graph and a list of cluster
assignments of the vertices.
The ordering of vertices and clusters is in descending order (as in `params`).
"""
function gen_graph_ta2(params::ABCDParams)
    clusters = populate_clusters_ta2(params)
    edges = params.isCL ? CL_model(clusters, params) : config_model(clusters, params)
    (edges=edges, clusters=clusters)
end