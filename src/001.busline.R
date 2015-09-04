# Explore the public transport network with bus lines.
library(dplyr)
library(ggplot2)
library(movr)

regions <- list(
  metro = c(120.069897,30.180852,120.236048,30.348045),
  urban = c(120.167722,30.255391,120.197546,30.281592),
  rural = c(120.16678,30.300872,120.200125,30.336536))

# Read public bus network data
ifile <- file("data/busnet_baidu_hz.txt", 'rb')
linn <- readLines(ifile)
busnet <- list()
linename <- ""
for (i in 1:length(linn)){
  if (i %% 3 == 1)
    linename <- strsplit(linn[i],'路')[[1]][1]
  else if( i %% 3 == 0){
    busnet[[linename]] <- strsplit(linn[i], '[ ,]')[[1]]
  }
}
close(ifile)

# Transform data format to data frame
busnet <- do.call(rbind, lapply(names(busnet), function(name){
  m <- matrix(as.numeric(busnet[[name]]), ncol=2, byrow=TRUE)
  df <- as.data.frame(m)
  df$bus <- name
  df
}))
colnames(busnet) <- c("lon", "lat", "bus")
saveRDS(busnet, 'rdata/busnet_baidu_hz.rds')

# Filter regional data
busnet <- filter(busnet, in_area(lon, lat, regions$metro))

# Plot bus network
ggplot(busnet, aes(lon, lat, group=bus, col=bus)) + theme_bw() +
  geom_path() + theme(legend.position="none")

