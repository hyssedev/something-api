import requests

url = "https://something-api.com/api/image-manipulation/gay?image=https://cdn.discordapp.com/avatars/418845865596420115/be456c6263b3e917a61a530a859a28d0.png?size=256" # the url you want to request from
headers = {'Authorization': 'Token yourtoken'} # add your token here

response = requests.get(url=url, headers=headers) # making the request to the url we specified with our specified headers

# improve this in production