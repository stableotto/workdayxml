def generate_rss(jobs):
    rss = """\
<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">

<channel>
<title>Workday Scraper - RSS Feed</title>
<link>https://github.com/christopherlam888/workday-scraper</link>
<description>An RSS feed for new Workday postings.</description>
"""

    for job_info in jobs:
        # Format title to only include job title
        job_title_text = job_info.get('job_title', 'Job Title Not Specified')

        # Get the raw HTML description
        job_description_html = job_info.get("job_posting_html", "")
        
        # If no HTML is available, provide a fallback message
        if not job_description_html:
            job_description_html = "<p>No description provided.</p>"

        job_location_text = job_info.get("job_location", "Location not specified")
        company_name = job_info.get("company", "Company not specified")
        rss += """\
<item>
    <title><![CDATA[{}]]></title>
    <link><![CDATA[{}]]></link>
    <description><![CDATA[{}]]></description>
    <location><![CDATA[{}]]></location>
    <company><![CDATA[{}]]></company>
</item>
""".format(
            f"{job_title_text}",
            f"{job_info['job_href']}",
            f"{job_description_html}",
            f"{job_location_text}",
            f"{company_name}",
        )

    rss += "\n</channel>\n</rss>"
    return rss
