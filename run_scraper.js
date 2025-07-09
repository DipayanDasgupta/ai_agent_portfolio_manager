// run_scraper.js

// This is a simple CommonJS wrapper to execute the ESM module from the command line.
const googleNewsScraper = require('google-news-scraper');

async function main() {
    try {
        // Get search term from command line arguments
        const searchTerm = process.argv[2];
        if (!searchTerm) {
            console.error(JSON.stringify({ error: "No search term provided." }));
            process.exit(1);
        }

        const articles = await googleNewsScraper({
            searchTerm: searchTerm,
            prettyURLs: true,
            timeframe: "7d", // Get news from the last 7 days
            puppeteerArgs: ["--no-sandbox", "--disable-setuid-sandbox"], // Required for many server environments
            logLevel: 'error', // Only log critical errors from the scraper
            limit: 15 // Get top 15 articles
        });

        // Output the result as a single JSON string to stdout
        console.log(JSON.stringify(articles, null, 2));

    } catch (error) {
        console.error(JSON.stringify({ error: `Scraper failed: ${error.message}` }));
        process.exit(1);
    }
}

main();