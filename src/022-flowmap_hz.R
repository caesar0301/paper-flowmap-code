library(plyr)
library(dplyr)
library(igraph)

# draw flowmap based on communities
flowmap.community <- function(flowmap) {
  fm.1 = flowmap
  graph <- as.undirected(graph.data.frame(fm.1[, c("from", "to")]))
  #plot(graph, vertex.label=NA, vertex.size=3, layout=layout.fruchterman.reingold, edge.arrow.mode="-")
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

fm <- read.csv("../data/fm_hz_i6h_m5.dat", sep=',', header=F, stringsAsFactors=F)
colnames(fm) = c("interval", "from", "to", "unique", "total")
fm$interval = as.POSIXct(fm$interval * 3600 * 6, origin="1970-01-01 00:00:00", tz="Asia/Shanghai")

pdf(file="figures/fm_hz_i6h_m5_0823.pdf", width=15, height=15)
par(mfrow=c(2,2))
for ( i in c("2012-08-23 02:00:00", "2012-08-23 08:00:00", "2012-08-23 14:00:00", "2012-08-23 20:00:00")) {
  fm.1 <- fm[fm$interval==as.POSIXct(i, tz="Asia/Shanghai"), ]
  flowmap.community(fm.1)
  title(main=sprintf("HZ: %s GMT", i))
}
dev.off()

