import html as html_escape
from html.parser import HTMLParser
from html.entities import name2codepoint

class HTMLFormatter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.indent = 0
        self.formatted = []
        self.indent_size = 2

    def handle_starttag(self, tag, attrs):
        self.formatted.append(' ' * self.indent + f'<{tag}>')
        self.indent += self.indent_size

    def handle_endtag(self, tag):
        self.indent -= self.indent_size
        self.formatted.append(' ' * self.indent + f'</{tag}>')

    def handle_data(self, data):
        if data.strip():
            self.formatted.append(' ' * self.indent + data.strip())

    def get_formatted_html(self):
        return '\n'.join(self.formatted)

def format_html(html_content):
    formatter = HTMLFormatter()
    formatter.feed(html_content)
    return formatter.get_formatted_html()

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

        # Format description with proper HTML structure
        raw_description = job_info.get("job_posting_text", "")
        
        # Split the description into sections
        sections = raw_description.split('\n\n')
        formatted_sections = []
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            # Check if this section is a header (usually in all caps or ends with ':')
            if section.isupper() or section.endswith(':'):
                formatted_sections.append(f'<h3>{section}</h3>')
            # Check if this section looks like a list (starts with bullet points or numbers)
            elif any(line.strip().startswith(('•', '-', '*', '1.', '2.', '3.')) for line in section.split('\n')):
                list_items = []
                for line in section.split('\n'):
                    line = line.strip()
                    if line:
                        # Remove bullet points or numbers and clean up
                        clean_line = line.lstrip('•-*1234567890. ')
                        # Add a dash at the start of each line for better readability
                        list_items.append(f'<li>- {clean_line}</li>')
                if list_items:
                    formatted_sections.append(f'<ul>{"".join(list_items)}</ul>')
            else:
                # Regular paragraph
                formatted_sections.append(f'<p>{section.replace(chr(10), "<br />")}</p>')
        
        formatted_description = "".join(formatted_sections)
        if not formatted_description:
            formatted_description = "<p>No description provided.</p>"

        # Format the HTML content
        formatted_html = format_html(formatted_description)

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
            f"{formatted_html}",
            f"{job_location_text}",
            f"{company_name}",
        )

    rss += "\n</channel>\n</rss>"
    return rss
