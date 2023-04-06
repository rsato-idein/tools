# MakeHuman を使った CG 生成

## 起動

```shell
docker run --rm -it --gpus device=0 --shm-size 2g -v /srv/work/rsato/tools/blender:/work --name sato_blender nytimes/blender:3.3.1-gpu-ubuntu18.04 /bin/bash
/bin/3.3/python/bin/pip3 install pillow
/bin/3.3/python/bin/pip3 install tqdm
```

## 実行

```shell
nohup /bin/3.3/python/bin/python3.10 batch.py 1 5 3 &
```

## メモ

BLENDERPIP "/bin/3.3/python/bin/pip3"
BLENDERPY "/bin/3.3/python/bin/python3.10"
