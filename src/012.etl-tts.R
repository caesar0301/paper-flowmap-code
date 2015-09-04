library(dplyr)

hh <- read.csv("data/tts/hh_public.csv", head=T, sep=",")
place <- read.csv("data/tts/place_public.csv", head=T, sep=",")
loc <- read.csv("data/tts/loc_public.csv", head=T, sep=",")

trips <- place %>%
  transmute( uid = sprintf("%d_%d", SAMPN, PERNO),
             locno = locno, DAYNO=DAYNO,
             stime = sprintf("2007-02-%02d %02d:%02d:00", DAYNO, ARR_HR, ARR_MIN),
             etime = sprintf("2007-02-%02d %02d:%02d:00", DAYNO, DEP_HR, DEP_MIN)) %>%
  left_join(loc[, c("LOCNO", "X_PUBLIC", "Y_PUBLIC")], by=c("locno" = "LOCNO"))

trips$stime <- as.numeric(strptime(trips$stime, "%Y-%m-%d %H:%M:%S", "GMT"))
trips$etime <- as.numeric(strptime(trips$etime, "%Y-%m-%d %H:%M:%S", "GMT"))

## merged TTS family trips
write.table(trips, "data/tts_trips.dat", sep=",", quote=F)