import cfscrape
from bs4 import BeautifulSoup as soup

NAME = 2
SUBS = 4
socialbladeURL = "http://www.socialblade.com"
twitchtrackerURL = "http://www.twitchtracker.com"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
}
cfscraper = cfscrape.create_scraper()

# Opens connection to given URL and returns parsed soup object of page HTML
def souper(url):
    print(url)
    html = cfscraper.get(url, headers=headers).content

    # parsing html
    return soup(html, "html.parser")


# Gets text from HTML section and converts from string to integer
def get_text(section):
    return int(section.text.strip().replace(",", ""))


# Gets total number of subscribers and views (last 30 days)
# from top 100 channels on YouTube, ranked by Social Blade
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
        name_div = divs[NAME]

        # parse values from divs
        subs = subs_div.text.strip()
        handle = name_div.a["href"].strip()
        views = get_monthly_views_sb(handle)

        # don't count channels that don't list subscriber count
        if subs != "--" and views is not None:
            # add values to total
            subs_total += int(subs.replace(",", ""))
            views_total += views
            n_channels += 1

            print(subs, views)
            print()

        i += 1

    return subs_total, views_total


# Given YouTube channel, checks how many views it got in the last 30 days
def get_monthly_views_sb(handle):
    handle = handle.replace("?app=desktop", "")
    url = socialbladeURL + handle

    page_soup = souper(url)
    views_div = page_soup.find("span", id="afd-header-views-30d")

    # if could't navigate to correct site, search for channel name and use first result's link
    if views_div is None:
        url = handle.replace("/c/", "/search/")
        if url == handle:
            url = handle.replace("/channel/", "/search/")
        if url == handle:
            url = handle.replace("/user/", "/search/")
        url = socialbladeURL + url

        # get link from first search result div
        search_page_soup = souper(url)
        first_result = search_page_soup.find("div", attrs={"style":"width: 800px; height: 25px;"})

        return get_monthly_views_sb(first_result.a["href"])

    else:
        views = int(get_text(views_div))

        # Social Blade has a bug that sometimes displays views as 0,
        # if so get views from monthly statistics page instead
        if views == 0:
            url += "/monthly"
            page_soup = souper(url)
            divs = page_soup.findAll("div", attrs={"style":"width: 240px; height: 40px; line-height: 40px; float: left;"})
            div_text = divs[1].text.strip()
            views = int(div_text[1 : len(div_text)].replace(",", ""))

    return views


# Estimates total revenue from subscribers of top 100 Twitch
# streamers and total number of followers shared among them
def scrape_twitchtracker():
    url = twitchtrackerURL + "/subscribers?page="
    tier1_subs = 0
    tier2_subs = 0
    tier3_subs = 0
    total_followers = 0

    # Scrapes data over 10 pages of highest subbed Twitch streamers
    for page in range(10, 11):
        page_soup = souper(url + str(page))
        channels = page_soup.find("table", id="channels").tbody.findAll("tr")
        # Iterates through each channel on page
        for channel in channels:
            vals = channel.findAll("td")

            # read all sub values from channel
            total_subs = get_text(vals[2].find("span"))
            gifted = get_text(vals[3])
            prime = get_text(vals[4])
            t1 = get_text(vals[5])
            t2 = get_text(vals[6])
            t3 = get_text(vals[7])

            # count all gifted subs as Tier 1, Prime subs also paid same as Tier 1
            tier1_subs += gifted + prime + t1
            tier2_subs += t2
            tier3_subs += t3

            # count subs unaccounted for (unshared) as Tier 1 subs
            shared = gifted + prime + t1 + t2 + t3
            unshared = max(total_subs - shared, 0)
            tier1_subs += unshared

            handle = vals[1].a["href"].replace("/subscribers", "")
            followers = get_followers(handle)
            total_followers += followers
            print(total_subs, gifted, prime, t1, t2, t3, unshared)

    # Calculate total revenue from number of subs
    total_revenue = (tier1_subs * 4.99) + (tier2_subs * 9.99) + (tier3_subs * 24.99)
    print(total_followers, total_revenue)
    print()

    return total_followers, total_revenue


# Given a Twitch streamer's username, checks total number of followers
def get_followers(handle):
    page_soup = souper(twitchtrackerURL + handle)
    blocks = page_soup.findAll("div", class_="g-x-l g-x-l-4")
    total_followers = blocks[1].findAll("div", class_="g-x-s-value")[2]
    return int(get_text(total_followers))


def main():
    yt_subs, yt_views = scrape_socialblade()
    twitch_followers, twitch_revenue = scrape_twitchtracker()

    lowCPM = 0.25
    highCPM = 4
    yt_revenue_lower = yt_views * lowCPM / 1000
    yt_revenue_upper = yt_views * highCPM / 1000

    print("YOUTUBE")
    print("subscribers:", yt_subs, "views:", yt_views)
    print("revenue to subs:", yt_revenue_lower/yt_subs, "-", yt_revenue_upper/yt_subs)

    print("\nTWITCH")
    print("followers:", twitch_followers)
    print("revenue to followers:", twitch_revenue/twitch_followers)

if __name__ == "__main__":
    main()
