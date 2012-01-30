import pstats
p = pstats.Stats('op.prof')
p.sort_stats('total').print_stats(20)
