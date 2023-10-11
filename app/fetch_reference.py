import html2text
import requests
from bs4 import BeautifulSoup
from django.utils.dateparse import parse_date
from readability import Document
from unidecode import unidecode

from app.models import Reference
from app.prompting import Prompt


def fetch_url_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        doc = Document(response.text)
        main_text = doc.summary()
        return response.text, main_text
    return None, None

def extract_info_with_bsoup(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract title
    title = soup.title.string if soup.title else None

    # Attempt to extract other meta data using common meta tag names
    publication_date = soup.find('meta', attrs={'name': 'date'}) or soup.find('meta', attrs={'property': 'article:published_time'})
    if publication_date:
        publication_date = parse_date(publication_date['content'])

    authors = soup.find('meta', attrs={'name': 'author'})
    if authors:
        authors = authors['content']

    # Source name could be extracted from the domain or other meta tags
    source_name = soup.find('meta', attrs={'property': 'og:site_name'})
    if source_name:
        source_name = source_name['content']

    return {
        'title': title,
        'publication_date': publication_date,
        'authors': authors,
        'source_name': source_name
    }

def extract_info_with_gpt(completer, html_content):
    format_instructions = '{"title": "Title", "publication_date": "YYYY-MM-DD", "authors": "Author Names", "source_name": "Source Name"}'
    system_prompt = f"""Given an HTML content, extract the following information: title, publication date, authors, and source name. You must give the publication_date in the provided format."""
    prompt = f"{html_content}"

    return completer(Prompt(format_instructions=format_instructions, system_prompt=system_prompt, user_prompt=prompt).messages)


def create_reference_from_url(url, completer, user):
    html_content, main_text = fetch_url_content(url)
    bsoup_info = extract_info_with_bsoup(html_content)

    # Convert the main text into markdown
    h = html2text.HTML2Text()
    markdown_content = h.handle(main_text)

    # If any info is missing from BeautifulSoup extraction, use GPT to fill in the gaps
    missing_keys = [key for key, value in bsoup_info.items() if value is None]
    if missing_keys:
        gpt_info = extract_info_with_gpt(completer, html_content[:3000])
        print(gpt_info)
        for key in missing_keys:
            value = gpt_info.get(key)
            if not value:
                continue

            if key == 'publication_date':
                value = parse_date(value)
            else:
                bsoup_info[key] = value
    reference = Reference.objects.create(
        user=user,
        title=bsoup_info['title'],
        content=unidecode(markdown_content),
        source_url=url,
        source_name=bsoup_info['source_name'],
        publication_date=bsoup_info['publication_date'],
        authors=bsoup_info['authors']
    )

    return reference
