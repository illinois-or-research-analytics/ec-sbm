for method in sbm+o
do
    echo "Cleaning ${method}"
    rm -rf data/backup/networks/${method}
    rm -rf data/backup/stats/${method}
done

# for method in orig orig_wo_outliers
# do
#     for clusterings in ikc_cm leiden_cpm_cm leiden_mod_cm sbm_old lfr leiden_cpm_
#     do
#         echo "Cleaning ${method}/${clusterings}"
#         rm -rf data/backup/networks/${method}/${clusterings}
#         rm -rf data/backup/stats/${method}/${clusterings}
#     done
# done