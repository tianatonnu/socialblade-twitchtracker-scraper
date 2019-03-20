import bs4
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup

NAME = 2
SUBS = 4
VIEWS = 5

socialbladeURL = "http://www.socialblade.com"
twitchtrackerURL = "http://www.twitchtracker.com/"
user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
headers = {'User-Agent': user_agent,}

# Gets total number of subscribers and views from
# top 100 channels on YouTube (ranked by Social Blade)
def scrape_socialblade():
    # channels are listed on Social Blade in divs with 4 styling types
    channel_styles = [
        "width: 860px; background: #f8f8f8;; padding: 10px 20px; color:#444; font-size: 10pt; border-bottom: 1px solid #eee; line-height: 40px;",
        "width: 860px; background: #fafafa; padding: 10px 20px; color:#444; font-size: 10pt; border-bottom: 1px solid #eee; line-height: 40px;",
        "width: 860px; background: #fafafa; padding: 0px 20px; color:#444; font-size: 10pt; border-bottom: 1px solid #eee; line-height: 30px;",
        "width: 860px; background: #f8f8f8;; padding: 0px 20px; color:#444; font-size: 10pt; border-bottom: 1px solid #eee; line-height: 30px;"
    ]
    url = socialbladeURL + "/youtube/top/500"
    subs_total = 0
    views_total = 0
    n_channels = 0
    i = 0

    # parsing html
    sb_soup = souper(url)

    # iterate through all channel divs
    channels = sb_soup.findAll(True, attrs={"style": channel_styles})
    while(n_channels < 100):
        channel = channels[i]

        # get views div and subs div from channel
        divs = channel.findAll("div")
        subs_div = divs[SUBS]
        # views_div = divs[VIEWS]
        name_div = divs[NAME]

        # parse values from divs
        subs = subs_div.text.strip().replace(",", "")
        # views = views_div.text.strip().replace(",", "")
        # views = divs.find("span", id="afd-header-views-30d").text.strip().replace(",", "")
        handle = name_div.a["href"].strip()

        # don't count channels that don't list subscriber count
        if subs != "--":
            # add values to total
            subs_total += int(subs)
            views_total += get_monthly_view_sb(handle)
            n_channels += 1

        i += 1

    # return subs_total, views_total
    return views_total


def get_monthly_view_sb(handle):
    page_soup = souper(handle)
    return page_soup.find("span", id="afd-header-views-30d").text.strip().replace(",", "")



# Opens connection to given URL and returns parsed soup object of page HTML
def souper(url):
    # connecting to url, grabbing page html
    request = Request(url, None, headers)
    client = urlopen(request)
    html = client.read()
    client.close()

    # parsing html
    return soup(html, "html.parser")


# Estimates total revenue from subscribers of top 100 Twitch
# streamers and total number of followers shared among them
def scrape_twitchtracker():
    url = "http://www.twitchtracker.com/subscribers?page="
    subs_total = 0
    views_total = 0
    page = 1
    n_streamers = 0

    # scrape 10 pages of top twitch streamers (top 100 total)

    # # for i in range(1):
    # while (n_streamers < 100):
    #     # parse next page
    #     page_url = ranked_url + str(page)
    #     page_soup = souper(page_url)
    #     streamers = page_soup.findAll("div", class_="ranked-item")
    #     i = 0
    #     # look at stats for each streamer on page
    #     while (i < len(streamers) and n_streamers < 100):
    #         streamer = streamers[i]
    #         tier1_subs = 0
    #         link = streamer.find("div", class_="ri-name").a["href"]
    #         streamer_url = base_url + link + "/subscribers"
    #         print(streamer_url)
    #
    #         subs_soup = souper(streamer_url)
    #         sections = subs_soup.findAll("div", class_="container")[3].findAll("section")
    #
    #         if len(sections) == 0:
    #             print("NO SECTIONS")
    #             break
    #         else:
    #             n_streamers += 1
    #             subs = sections[2].table.tbody.tr
    #
    #         print(subs)
    #         i += 1
    #     page += 1

    for i in range(10):
        page_url = url + str(page)
        page_soup = souper(page_url)
        channels = page_soup.find("table", id="channels").findAll("tr")
        for channel in channels:
            values = channel.findAll("td")

            for v in values:
                print(v.text.strip())


def get_followers(handle):
    url = "http://www.twitchtracker.com/" + handle
    page_soup = souper(url)

    return int(page_soup.find("div", class_="g-x-s-value").text.strip().replace(",", ""))


def main():
    # print(scrape_socialblade())
    scrape_twitchtracker()


if __name__ == "__main__":
    main()
