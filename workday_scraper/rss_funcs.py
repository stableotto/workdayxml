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

        # Format description with <p> tags for double newlines and <br /> for single newlines
        raw_description = job_info.get("job_posting_text", "")
        paragraphs = raw_description.split('\n\n') # Split by double newline
        processed_paragraphs = []
        for para in paragraphs:
            # Replace single newlines within a paragraph with <br />
            processed_para = para.strip().replace('\n', '<br />')
            if processed_para: # Avoid empty <p> tags
                processed_paragraphs.append(f'<p>{processed_para}</p>')
        formatted_description = "".join(processed_paragraphs)
        if not formatted_description: # Fallback if description was empty
            formatted_description = "<p>No description provided.</p>"

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
            f"{job_title_text}", # Changed to only job title
            f"{job_info['job_href']}",
            f"{formatted_description}", # Use new formatted description
            f"{job_location_text}",
            f"{company_name}",
        )

    rss += "\n</channel>\n</rss>"
    return rss
