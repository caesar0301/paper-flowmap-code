# Explore POI in HZ city
# Xiaming Chen
##
library(dplyr)
library(ggplot2)
library(animation)
library(movr)

regions <- list(
  metro = c(120.069897,30.180852,120.236048,30.348045),
  urban = c(120.167722,30.255391,120.197546,30.281592),
  rural = c(120.16678,30.300872,120.200125,30.336536))

# read data
poi <- read.csv("data/poi_hz.txt", encoding="UTF-8", sep="\t", header=FALSE,
                  stringsAsFactors=FALSE)
colnames(poi) <- c("category", "lon", "lat", "name")
poi$category <- factor(poi$category)

# filter area
poi.m <- poi %>% filter(in_area(lon, lat, regions$metro))

# Order categories by count
cats <- sort(unique(poi.m$category))

# plot animated plot
saveGIF({
  i = 0
  for ( cat in cats ){
    poi.c <- filter(poi.m, category == cat)
    if ( i == 0){
      gg <- ggplot(poi.c, aes(lon, lat, group=category, color=category)) + 
        theme_bw() + geom_point() +
        xlab("East-West") + ylab("North-South") +
        theme(legend.text=element_text(size=16),
              axis.title=element_text(size=14))
    } else {
      gg <- gg + geom_point(data = poi.c, aes(lon, lat))
    }
    plot(gg)
    i <- i + 1
  }
}, movie.name="figures/poi_categories_metro.gif", interval=2, ani.width=800,
ani.height=600)
