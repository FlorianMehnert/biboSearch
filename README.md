# biboSearch
- access the search option of [bibo dresden](https://katalog.bibo-dresden.de) for movies
## Streamlit
### install packages (streamlit app)
```bash
pip install bs4 streamlit requests
```
### run the app
```bash
streamlit run main.py
```
## BeeWare Apps
```bash
briefcase build android --update-resources && briefcase run android
```

## changing the icon
- requires multiple icons of **various sizes**: to create them I chose to use [svg2png](https://github.com/sterlp/svg2png) with [svg2pngConfig.json](./svg2pngConfig.json)
