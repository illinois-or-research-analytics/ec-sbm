struct ABCDParams3
    w::Vector{Int}
    s::Vector{Int}
    clusters::Vector{Vector{Int64}}
    μ::Union{Float64, Nothing}
    ξ::Union{Float64, Nothing}
    isCL::Bool
    islocal::Bool
    hasoutliers::Bool

    function ABCDParams3(w, s, clusters, μ, ξ, isCL, islocal, hasoutliers=false)
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
            news = sort(s, rev=true)
            
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
            μ, ξ, isCL, islocal, hasoutliers)
    end
end

function populate_clusters_ta3(params::ABCDParams3)
    clusters = fill(-1, length(params.w))
    for (v, c) in params.clusters
        clusters[v] = c
    end
    @assert minimum(clusters) == 1
    return clusters
end

function gen_graph_ta3(params::ABCDParams3)
    clusters = populate_clusters_ta3(params)
    edges = params.isCL ? CL_model(clusters, params) : config_model_ta2(clusters, params)
    (edges=edges, clusters=clusters)
end