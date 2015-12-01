library(dplyr)

################################################
#  Individual location number and node degree
################################################

ndgr_week <- read.csv('data/hcl_mesos0822_ndgr', sep=',', head=T)
ndgr_week$isweek <- 1
ndgr_wend <- read.csv('data/hcl_mesos0825_ndgr', sep=',', head=T)
ndgr_wend$isweek <- 0

ndgr <- rbind(ndgr_week, ndgr_wend)
ndgr$isweek <- as.factor(ndgr$isweek)

# CDF of nloc
p <- ggplot(ndgr, aes(nloc, group=isweek, color=isweek)) +
  stat_ecdf() + theme_bw() + grid() + 
  scale_x_log10(name="N", limit=c(2,100)) +
  scale_y_continuous(name="User CDF") +
  scale_color_discrete(breaks=c(1, 0),
                       name="",
                       labels=c("Weekday","Weekend"))
p <- p + theme(legend.position=c(0.7, 0.3))
ggsave('figures/hcl_mesos_nloc.pdf', plot=p, width=3.5, height=2.5)


# CCDF of ndgr
p <- ggplot(ndgr, aes(ndgr, group=isweek, color=isweek)) +
  stat_ecdf() + theme_bw() + grid() +
  scale_x_log10(name="D", limit=c(1,10)) +
  scale_y_continuous(name="User CDF") +
  scale_color_discrete(breaks=c(1, 0),
                       name="",
                       labels=c("Weekday","Weekend"))
p <- p + theme(legend.position=c(0.7, 0.3))
ggsave('figures/hcl_mesos_ndgr.pdf', plot=p, width=3.5, height=2.5)