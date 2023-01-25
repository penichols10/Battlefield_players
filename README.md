# Introduction
In this notebook I scrape the battlefieldttracker Battlefield 5 [Leaderboard](https://battlefieldtracker.com/bfv/leaderboards/stats/all/Wins?page=1) as well as all of the profiles (ex. [this](https://battlefieldtracker.com/bfv/profile/psn/themadbat2/overview)).

For web scraping I retrieve information from the site's "hidden API," using Selenium to get around an issue of the JSON not loading, and I store the data in a SQL database.

# Contents

* Scraper Files

    * [scraper.py](scraper.py): python script for web scraping
    * [categories_to_scrape.txt](categories_to_scrape.txt): JSON keys to keep while scraping

* Database Files
    * [bfvstats.db](bfvstats.db): SQLite database containing player performance metrics
    * [useful_queries_sqlite.sql](useful_queries_sqlite.sql): SQL queries for getting useful summary information out of the above database.
    * [create_sqlite_bfvstats_tables.py](create_sqlite_bfvstats_tables.py): Creates a new, empty database with appropriate tables using python. You should have no need for this, but it may be useful if you want to scrape newer data.
    * [create_bfvstats_sqlite.txt](create_bfvstats_sqlite.txt): Query to be used with the above script. You should have no need for this, but it may be useful if you want to scrape newer data.

* EDA Notebook
    * [analysis.ipynb](analysis.ipynb): Notebook containing some preliminary exploratory data analysis. This would need to be fleshed out a bit for downstream tasks, but it addresses issues with the dataset like feature engineering, outliers, bin number selection due to those outliers, high correlations between features, and missing values.

# To do
Nothing, at the moment.

