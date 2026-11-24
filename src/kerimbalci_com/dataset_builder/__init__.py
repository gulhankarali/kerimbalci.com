"""Tools for generating eval datasets from the site.

Flow (see instructions/dataset.md):
    1. crawl  : sitemap -> all pages -> plain text (+ manifest.json)
    2. split  : splits the texts into groups balanced by word count
    3. (LLM)  : for each group, instructions/dataset.md -> "Generator Prompt"
    4. merge  : writes the generated JSON into the dataset after evidence verification
    5. verify : checks every evidence quote of a dataset against the site text
"""
