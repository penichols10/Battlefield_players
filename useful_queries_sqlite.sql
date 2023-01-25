-- Check for differences in player counts, average time played, average Score Per Minute, kill/death, ratio, and Accuracy between platforms
-- Reasoning here is that player performance may be lower on non-PC platforms.
-- What is in fact is that average scores per minute are higher on PC, but there's not clearly a statistically significant difference in average accuracies.
-- Kill/death ratios are on average substantially higher on PC. 
SELECT 
	platform, 
	COUNT(player_id) as player_counts, 
	AVG(timePlayed_value)/3600 as avg_time_played_hours,
	AVG(scorePerMinute_value) as avg_score_per_min,
	AVG(kdRatio_value) as avg_kdr,
	AVG(shotsAccuracy_value) as avg_accuracy
FROM bfvstats
GROUP BY platform;

-- Returns the top 10 players ranked by score per minute
-- Game has a cheating problem, so this can be used to sanity check player performance
SELECT
	player_id,
	scorePerMinute_value,
	scorePerMinute_value/ (SELECT AVG(scorePerMinute_value) FROM bfvstats) as rate_over_avg_spm
FROM bfvstats
ORDER BY scorePerMinute_value DESC
LIMIT 10;


-- Compares average assault kills per minute and scores per minute between players with above or below average kill death ratios, broken out by player platform
-- Note that we have the same columns for all of the infantry classes (assault, medic, recon, support), so a find-replace makes this query useful beyond assault
-- The CTE allows for grouping by an alias (here, the case statement), which is a bit more readable
WITH assault_stats AS (
	SELECT
		player_id, 
		platform, 
		Assault_kills_value, 
		Assault_deaths_value, 
		Assault_killsPerMinute_value, 
		Assault_kdRatio_value, 
		Assault_kdRatio_percentile, 
		Assault_timePlayed_value, 
		Assault_shotsFired_value, 
		Assault_shotsHit_value, 
		Assault_shotsAccuracy_value, 
		Assault_score_value, 
		Assault_score_percentile,
		Assault_scorePerMinute_value, 
		Assault_scorePerMinute_percentile,
		CASE 
			WHEN Assault_kdRatio_value > (SELECT AVG(Assault_kdRatio_value) FROM bfvstats) THEN 'better'
			ELSE '(equal to or) worse'
		END AS beats_average_assault_kdr
	FROM bfvstats
)
SELECT 
	platform,
	beats_average_assault_kdr, 
	AVG(Assault_killsPerMinute_value) AS Average_Assault_Kills_per_Minute, 
	AVG(Assault_scorePerMinute_value) as Average_Assault_Score_Per_Minute
	
FROM assault_stats
GROUP BY beats_average_assault_kdr, platform
ORDER BY platform, beats_average_assault_kdr;

-- Simple query to check number of records
SELECT COUNT(*) AS num_skips FROM bfvstats ;

-- Simple query to check the latest log entry
SELECT skip as last_skip FROM log ORDER BY skip DESC LIMIT 1;

-- Simple query to check the log table
SELECT * FROM log ORDER BY skip DESC;