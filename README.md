# HoopReacher

Personal NBA standings picks with a static website at https://hoopreacher.com/.

## MVP Ladder

The supplied `NBA_MVP3.csv` provides the 2026–27 fallback snapshot and position labels.
The published live ladder and its opponent splits use ESPN's completed regular-season NBA
box scores. Each opponent row groups games against that team. The overall row shows games
played, per-game averages weighted by appearances, and shooting percentages calculated
from total makes and attempts. Overall MVP is the ladder's AVG. The publisher uses one
shared snapshot with a 12-hour cache, and open MVP pages reload every 12 hours.
Both table views export CSV.
