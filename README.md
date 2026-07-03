# League Fair Teams

A web app that builds balanced League of Legends custom games from a list of
summoners. Enter each player's Riot ID, pull their live ranked stats, and the
app calculates a performance-weighted MMR for everyone and deals the players
into two teams of five so the teams come out as even as possible.

## The problem it solves

Picking fair teams in custom 5v5 lobbies is usually a guessing game. Someone
reads off ranks, the highest-rated players get stacked on one side, and the
match becomes a stomp. Rank alone is also a weak signal: two players in the
same division can be far apart in actual skill. This tool replaces that guess
with a data-driven MMR estimate and an automatic balancer that splits ten
summoners into two teams of roughly equal total strength.

## What it does

- **Riot ID lookup.** Resolve a summoner by Game Name and Tag Line through the
  Riot Account API, then pull their summoner, league, and profile icon data.
- **Performance-weighted MMR.** Starts from a base derived from tier, division,
  league points, and summoner level, then refines it from recent ranked solo
  games: KDA, gold per minute, damage per minute, and win rate. Match details
  are fetched concurrently with a thread pool to keep the lookup fast.
- **Automatic team balancing.** A greedy snake-draft sorts all summoners by MMR
  and deals them into two teams of five, always placing the next player on the
  side with the lower running MMR total so the two teams end up close.
- **Live team view.** Drag and drop players between teams (SortableJS), with
  rank badges, win rates, and per-team MMR totals shown inline. Teams persist
  in localStorage between sessions.

## Tech stack

- **Python / Flask** backend served as a JSON API blueprint
- **Flask app factory** pattern with blueprints for routes
- **requests** for Riot Games API calls (account, summoner, league, match v5)
- **concurrent.futures** ThreadPoolExecutor for parallel match-detail fetching
- **Vanilla JS** frontend (no build step) with SortableJS for drag and drop
- **python-dotenv** for local configuration

## How to run

1. Get a Riot Games API key from the
   [developer portal](https://developer.riotgames.com/) (a Development API key
   is enough for personal use).
2. Create a `.env` file in the project root with your key:
   ```
   RIOT_API_KEY=your_key_here
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Start the server:
   ```
   python app.py
   ```
5. Open the served local URL and start adding summoners.

## API surface

The frontend hits a single endpoint, `POST /get_summoner_data`, which expects a
JSON body of `game_name`, `tag_line`, and an optional `num_of_matches` (defaults
to 20). It returns the resolved summoner with tier, division, LP, win rate, and
the calculated MMR.

## Notes and limitations

- The MMR formula is a heuristic that blends LP and in-game performance
  metrics, not Riot's internal MMR (which is not exposed). It is meant to be a
  fairer signal than rank on its own, not an authoritative number.
- Match fetching is scoped to Ranked Solo/Duo (queue 420). Players with few or
  no recent ranked games fall back to their LP-based base MMR.
- The Riot API is region-specific; this app targets NA summoners and the
  Americas routing for account and match endpoints.
- A simple sliding-window rate limiter is included to stay polite with the Riot
  API's per-second and per-two-minute request budgets.
