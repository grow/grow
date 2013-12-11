import markdown

def markdown_filter(value):
  return markdown.markdown(value.decode('utf-8'))
