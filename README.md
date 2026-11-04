NBA 2026-27 PREDICTIONS - STANDALONE HTML
=======================================
_README updated: October 28, 2026_

**1. WHAT THIS FILE IS**
--------------------
index.html is a self-contained, interactive copy of the NBA
dashboard. Its page templates, styling, scripts, fonts, and saved data are
embedded in one HTML file. Internal pages display inside an embedded frame.

This is a saved snapshot, not a continuously updating live service. An internet
connection is not needed to browse the included data. No Node.js installation,
local server, account, or additional project files are required for viewing.

**2. NAVIGATION AND CONTROLS**
-------------------------
- Click or tap the circular menu button to open Live Predictions, Current
  Standings, and Today's Schedule. Hover reveals the Menu label on desktop.
- Click outside the menu, or press Escape, to close it.
- Click a team name to open its included team page.
- Use the page's Back link to return to the appropriate dashboard section.
- Roster and Schedule tabs show one panel at a time on prediction team pages.
- Scroll tables horizontally when they are wider than your screen. Roster
  number and player-name columns remain visible while stat columns scroll.
- Use Tab and Enter to navigate and activate keyboard-accessible controls.
- Sorting and tab selections are viewing controls; they do not edit predictions
  or save a new HTML file. Some view state resets on navigation or reopening.

**4. INCLUDED PAGES**
-----------------
Live Predictions:
Shows the predicted East and West top eight, with three alternatives for #8.
The season selector switches between regular-season and preseason comparisons.
The predictions remain the same; the comparison data changes by season phase.
Prediction team links open the corresponding regular or preseason roster and
schedule. Column headings toggle ascending/descending sorting independently
for each conference. Missing values remain last. W-L sorts by wins, with losses
used as a tie-breaker. Sorting does not change a team's predicted position.

Current Standings:
Includes all 30 teams in East and West tables using regular-season standings.
Teams link to roster-only pages. These pages do not offer a Schedule tab.

Today's Schedule:
Shows the league schedule for the date captured during export, using Eastern
Time. It does not advance to a new date when the HTML is reopened tomorrow.
Click a matchup to view its captured game statistics. Only games included in
this captured daily schedule have game-detail snapshots; this is not a complete
historical archive of every NBA box score.

Game Statistics:
Shows the home team and score versus the away score and team, followed by each
team's player table. Headers sort the individual tables. These are single-game
totals, not season averages. A scheduled or unfinished game's details reflect
what was available when exported; later results are not added automatically.

**5. CURRENT PREDICTIONS**
----------------------

|Eastern Conference       | Western Conference |
|:------------------------|:-----------------------|
|1. Detroit Pistons       |1. Oklahoma City Thunder|
|2. Philadelphia 76ers    |2. San Antonio Spurs |
|3. Toronto Raptors       |3. Minnesota Timberwolves |
|4. New York Knicks       |4. Denver Nuggets  |
|5. Boston Celtics        |5. Houston Rockets  |
|6. Indiana Pacers        |6. Los Angeles Lakers |
|7. Miami Heat            |7. Portland Trail Blazers |
|8. Cavaliers             |8. Clippers  |
|  OR Wizards             | OR Mavericks |
|  OR Magic           | OR Grizzlies |

This list describes the configuration when this README was written. Future
exports may contain revised predictions; the HTML is the authoritative copy.

**6. READING THE PREDICTION TABLES**
--------------------------------
Pick: the predicted conference position. Alternatives share the eighth slot.
Team: linked team name.
Now: provider's current conference seed, when available.
W-L: wins and losses for the selected phase.
Win %: wins divided by games played, expressed as a percentage.
Gap: current position minus predicted position. A negative number means the
team ranks higher than predicted. Match means the positions are equal.

Exact positions counts matching prediction slots among comparable slots.
The comparison denominator may be less than 16 when rankings are unavailable.
For an alternative slot, all its candidate teams need available ranks before
that slot is counted as comparable; any candidate at #8 produces one match.
Current match rate is matches divided by comparable slots. It is a description
of the saved standings, not a probability or forecast of the final standings.

Positions follow the provider's conference seed field. Early-season ties and
tiebreakers can affect ordering. A missing rank or dash is not automatically a
zero, loss, or last-place position. Preseason and regular season are separate.

**7. ROSTER STATISTICS**
--------------------
Player labels combine name and position, for example: Player Name - PG.
Position can reflect the projected depth-chart assignment. Default order is
projected starters, followed by bench depth; unlisted players appear afterward.
This is not a guarantee of the actual starting lineup for a particular game.
Use Sort players for first-name/last-name ordering or click a column heading.

No.   Jersey number
GP    Games played
MPG   Minutes per game
PPG   Points per game
APG   Assists per game
RPG   Rebounds per game
FG%   Field-goal percentage
3P%   Three-point percentage
2P%   Two-point percentage
FT%   Free-throw percentage
STL   Steals per game
BLK   Blocks per game
TOV   Turnovers per game
eFG%  Effective field-goal percentage

Roster averages are calculated from completed box scores with the selected
team and season phase. They are not combined across former teams for traded
players. DNP entries are excluded from games-played calculations. Percentages
use summed makes and attempts, rather than averaging each game's percentage.
eFG% = (field goals made + 0.5 x three-pointers made) / field-goal attempts x 100.
No attempts or unavailable statistics are displayed as dashes. Most averages
and percentages display one decimal place. Names and PPG/APG/RPG are red.
The current roster listing may change independently of the games represented.

**8. SCHEDULES AND GAME TABLES**
----------------------------
Team schedules show opponent, W/L, status/score, home/away, time, and date.
W is green and L is red for completed results; pending games have no outcome.
Dates use dd/mm/yyyy. Times use America/New_York, including EST or EDT as
appropriate. Home/away and W/L are from the selected team's perspective.

Game tables contain jersey number, player name with position, minutes, points,
assists, rebounds, FG%, 3P%, FT%, steals, blocks, and turnovers. DNP means did
not play. Missing values and zero-attempt shooting percentages are dashes.

**9. OFFLINE LIMITATIONS AND DATA FRESHNESS**
----------------------------------------
- Reloading the file does not download new data.
- Live-server refresh buttons and automatic update controls are hidden.
- The live site's periodic refresh behavior does not run in this snapshot.
- Page update timestamps describe captured responses; export requests can have
  different timestamps and may include data from the live server's cache.
- External ESPN source links require internet access and leave the snapshot.
- Provider delays, unavailable stats, corrections, and source errors can affect
  what is captured. A successful export does not certify every statistic.
- Live edits do not change previously shared copies of the HTML.

**10. TROUBLESHOOTING**
-------------------
Blank page or unresponsive controls:
Download the complete file and open it in a full browser with JavaScript
allowed. Avoid attachment previews. Try another browser or a desktop device.

Old predictions or old scores:
Confirm you opened the newest standalone file. Close old tabs and reopen it.
If needed, regenerate the snapshot; browser refresh alone cannot update data.

A game or team page says data is unavailable:
It may be outside the exported routes, or the provider may not have supplied
the data at capture time. Return through the menu and select an included link.
For missing expected content, refresh the live data and export again.

Table looks too wide:
Scroll within the table, rotate the device, or use a wider browser window.
Dense statistical tables intentionally retain horizontal scrolling.

**APX A. SOURCE AND SCOPE**
--------------------
The dashboard uses ESPN NBA data and user-supplied predictions. It is a personal
prediction tracker, not an official NBA or ESPN product. Source links are
provided on relevant pages. Data should be interpreted with its capture time,
season phase, and availability in mind.
