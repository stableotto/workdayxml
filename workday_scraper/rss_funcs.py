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
        job_posting_text = job_info["job_posting_text"].replace("\n", "<br>")
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
            f"{job_info['company']}: {job_info['job_title']}",
            f"{job_info['job_href']}",
            f"{job_posting_text}",
            f"{job_location_text}",
            f"{company_name}",
        )

    rss += "\n</channel>\n</rss>"
    return rss
