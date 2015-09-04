library(plyr)
library(movr)
library(igraph)
library(magicaxis)

# load data
mov_site <- readRDS("rdata/dsp10cl.rds")

##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# stat of compressed movement

# compress individual's movement
mov_site2 <- mov_site %>%
  group_by(usr) %>%
  do(compress_mov(x=.$site, t=.$time))
saveRDS(mov_site2, "rdata/dsp10cl_compressed.rds")

cs <- mov_site2 %>%
  group_by(usr) %>%
  summarize(
    n=length(loc),
    u=length(unique(as.numeric(loc))),
    dwell = mean(etime-stime) / 60
  )
magplot(ecdf(cs$n), log="x", xlim=c(1, max(cs$n)), main="Total sessions")
magplot(ecdf(cs$u), log="x", xlim=c(1, max(cs$u)), main="Unique locations")
magplot(ecdf(cs$dwell), log="x", xlim=c(1, max(cs$dwell)), main="Dwell time (min)")
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# generate flow map

# draw flowmap based on communities
flowmap.community <- function(flowmap) {
  fm.1 = flowmap
  graph <- as.undirected(graph.data.frame(fm.1[, c("from", "to")]))
  plot(graph, vertex.label=NA, vertex.size=3, layout=layout.fruchterman.reingold, edge.arrow.mode="-")
  communities <- infomap.community(graph, e.weights=fm.1$unique)
  mem <- data.frame(v=as.numeric(V(graph)$name), comm=communities$membership)
  
  fm.2 <- fm.1 %>% mutate(
    from = mapvalues(from, mem$v, mem$comm, warn_missing = F),
    to = mapvalues(to, mem$v, mem$comm, warn_missing = F)) %>%
    group_by(from, to) %>% dplyr::filter(from != to) %>%
    dplyr::summarise(total = sum(total), unique=sum(unique))
  
  graph.2 <- as.undirected(graph.data.frame(fm.2[, c("from", "to")]))
  plot(graph.2, vertex.label=NA, vertex.size=3, layout=layout.fruchterman.reingold,
       edge.arrow.mode="--", edge.width=log(fm.2$unique))
}

fm <- read.csv("../data/fm_dsp01_i6h_m5.dat", sep=',', header=F, stringsAsFactors=F)
colnames(fm) = c("interval", "from", "to", "unique", "total")
fm$interval = as.POSIXct(fm$interval * 3600 * 6, origin="1970-01-01 00:00:00", tz="GMT")

pdf(file="figures/fm_dsp01_i6h_m5_0110.pdf", width=15, height=30)
par(mfrow=c(4,2))
for ( i in c("2013-01-10 00:00:00", "2013-01-10 06:00:00", "2013-01-10 12:00:00", "2013-01-10 18:00:00")) {
  fm.1 <- fm[fm$interval==as.POSIXct(i, tz="GMT"), ]
  flowmap.community(fm.1)
  title(main=sprintf("DSP: %s GMT", i))
}
dev.off()
