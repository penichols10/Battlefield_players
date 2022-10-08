# Introduction
In this notebook I scrape the battlefieldttracker Battlefield 5 [Leaderboard](https://battlefieldtracker.com/bfv/leaderboards/stats/all/Wins?page=1) as well as all of the profiles (ex. [this](https://battlefieldtracker.com/bfv/profile/psn/themadbat2/overview)) and perform some exploratory data analysis on the resulting information.

For web scraping I retrieve information from the site's "hidden API," using Selenium to get around an issue of the JSON not loading, and I store the data in a SQL database. Po

# Contents

**scrapery.py**: used to scrape the site

**analysis.ipynb**: notebook containing analysis (WIP)

**dfvstats.db**: contains the actual data as well as some logging information.

**categories_to_scrape.txt**: text file containing names of keys I want to target while scraping. A bit preferable to collecting these automatically from JSON at the beginning of every run

**data/**: contains files from when I was storing the data in .csv format. To be removed in the future.

**database_backup**: I am considering potential future changes to the database, so I am keeping a reasonably recent backup until I am satisfied with my set up.

**scraper_explanation.py**: Old version of the scraper. Should be deprecated.

# To do
Finish scraping the site.

Despite the scraping not being finished, I am working on the analysis notebook as I can start on outlier detection using some domain knowledge, I can reasonably expect the frequency of NaN's to stay low, I can code up analysis that I know needs to be done even if I don't know the outcome, etc.

