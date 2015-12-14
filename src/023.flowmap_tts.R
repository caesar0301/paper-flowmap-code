library(plyr)
library(dplyr)
library(igraph)
library(movr)

trips <- read.csv("../data/tts_trips.dat", head=T, sep=",")
trips <- trips[complete.cases(trips), ]
fm <- trips %>% group_by(DAYNO) %>%
  do(with(., flowmap2(uid, locno, as.numeric(stime), as.numeric(etime), gap=6*3600))) %>%
  saveRDS(fm, "data/tts_fm.rds")

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
    group_by(from, to) %>%
    dplyr::summarise(total = sum(total), unique=sum(unique))
  
  graph.2 <- as.undirected(graph.data.frame(fm.2[, c("from", "to")]))
  plot(graph.2, vertex.label=NA, vertex.size=3, layout=layout.fruchterman.reingold,
       edge.arrow.mode="--", edge.width=log(fm.2$unique))
}

fm <- readRDS("data/tts_fm.rds") %>% dplyr::filter(total>2 & from != to) %>%
  mutate(from = as.numeric(from), to = as.numeric(to))
flowmap.community(fm[fm$DAYNO==2, ])