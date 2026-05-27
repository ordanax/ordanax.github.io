Jekyll::Hooks.register :pages, :pre_render do |page, payload|
  payload["seo"] = generate_json_ld(page, payload)
end

Jekyll::Hooks.register :documents, :pre_render do |document, payload|
  payload["seo"] = generate_json_ld(document, payload)
end

def generate_json_ld(page, payload)
  site = payload["site"]
  url = site["url"]
  page_url = page.url

  if page.data["layout"] == "post" || page.data["tags"]
    json_ld = {
      "@context" => "https://schema.org",
      "@type" => "Article",
      "headline" => page.data["title"] || site["title"],
      "description" => page.data["description"] || site["description"],
      "url" => "#{url}#{page_url}",
      "mainEntityOfPage" => {
        "@type" => "WebPage",
        "@id" => "#{url}#{page_url}"
      }
    }

    if page.data["tags"]
      json_ld["keywords"] = page.data["tags"].join(", ")
    end

    if page.data["date"]
      json_ld["datePublished"] = page.data["date"].to_s
    end

    json_ld
  else
    json_ld = {
      "@context" => "https://schema.org",
      "@type" => "WebPage",
      "name" => page.data["title"] || site["title"],
      "description" => page.data["description"] || site["description"],
      "url" => "#{url}#{page_url}"
    }

    if page_url == "/"
      json_ld["@type"] = "WebSite"
      json_ld["name"] = site["title"]
      json_ld["description"] = site["description"]
      json_ld["url"] = url
      json_ld["potentialAction"] = {
        "@type" => "SearchAction",
        "target" => "#{url}/search.html?q={search_term_string}",
        "query-input" => "required name=search_term_string"
      }
    end

    json_ld
  end
end
