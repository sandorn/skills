using HtmlAgilityPack;
using System.Net.Http;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace MyWpfApp.Services
{
    public class WebScraperService
    {
        private readonly HttpClient _httpClient;
        
        public WebScraperService()
        {
            _httpClient = new HttpClient();
            _httpClient.DefaultRequestHeaders.Add("User-Agent", 
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
        }
        
        public async Task<string> GetHtmlAsync(string url)
        {
            return await _httpClient.GetStringAsync(url);
        }
        
        public async Task<List<string>> ExtractLinksAsync(string url)
        {
            var html = await GetHtmlAsync(url);
            var doc = new HtmlDocument();
            doc.LoadHtml(html);
            
            var links = new List<string>();
            var nodes = doc.DocumentNode.SelectNodes("//a[@href]");
            
            if (nodes != null)
            {
                foreach (var node in nodes)
                {
                    links.Add(node.GetAttributeValue("href", ""));
                }
            }
            
            return links;
        }
    }
}
