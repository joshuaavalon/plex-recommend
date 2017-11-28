# plex-recommend

Plex Recommend is a python script that generates recommendation playlist based on what the users watched.

## Requirements
* Python 3.6 (Only tested on Python 3.6. Previous version may work)
  
## Usage
1. Install dependencies (Recommend using virtualenv).
```
pip install -r requirements.txt
```
2. Add your Plex address and Plex token to the recommend.py.
3. Run `python recommend.py`.
4. (Optional) Setup cron job to run it.

## FAQ
#### Q. How does it generates a recommendation playlist?
A. It based on what the user have watched to calcuate his preferences and find the unwatch series / movies match most.

#### Q. How is it different from Plex's "Related"
A. Plex's "Related" heavily flavor actors over gernes which is stupid in my opinion. 
How does an action movie related to a romance movie just because they have some common actors?

#### Q. How to adjust the parameters?
A. Read the code. the calculation is not that difficult.

## Known Issues
#### Generate playlist for **ALL** libraries.
Plex API does not include if the library is included in dashboard or not. You can filter it manually in `analysis()` by the `section.title`
