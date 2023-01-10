# ReadMe

## data

<https://www.youtube.com/watch?v=B998-9DmecM>

## command

```shell
mkdir obama_images
ffmpeg -i obama.mp4 -ss 00:00:10 -t 30 -r 10 ./obama_images/%3d.jpg
```

'''python
python inference.py model/pose.nnoir model/light_rfb.nnoir model/light_rfb_6D.nnoir model/6drepnet_s0.nnoir obama_images/
'''
