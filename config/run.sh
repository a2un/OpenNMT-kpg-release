#!/usr/bin/env bash
# train
CUDA_VISIBLE_DEVICES=0,1 nohup python train.py -config config/config-transformer-keyphrase.yml > output/nohup.kp20k.one2one.transformer.log &
CUDA_VISIBLE_DEVICES=2,3 nohup python train.py -config config/config-transformer-keyphrase-magkp.yml > output/nohup.mag.one2one.transformer.log &
CUDA_VISIBLE_DEVICES=4,5 nohup python train.py -config config/config-rnn-keyphrase.yml > output/nohup.kp20k.one2one.rnn.log &
CUDA_VISIBLE_DEVICES=6,7 nohup python train.py -config config/config-rnn-keyphrase-magkp.yml > output/nohup.mag.one2one.rnn.log &

# test
CUDA_VISIBLE_DEVICES=5 nohup python kp_run_eval.py -config config/test/config-rnn-keyphrase.yml -data_dir data/keyphrase/meng17/ -ckpt_dir models/keyphrase/1st/ -output_dir output/keyphrase/1st/ -verbose -testsets nus semeval duc -batch_size 64 > output/keyphrase/kp_run_eval-nus_semeval_duc.log &
1753

nohup python kp_run_eval.py -config config/test/config-rnn-keyphrase.yml -data_dir data/keyphrase/meng17/ -ckpt_dir models/keyphrase/1st/ -output_dir output/keyphrase/1st/ -testsets nus semeval duc -batch_size 64 > output/keyphrase/kp_run_eval-nus_semeval_duc.log &

nohup python kp_run_eval.py -config config/test/config-rnn-keyphrase.yml -data_dir data/keyphrase/meng17/ -ckpt_dir models/keyphrase/1st/ -output_dir output/keyphrase/1st/ -testsets inspec -batch_size 64 > output/keyphrase/kp_run_eval-inspec.log &
111142

nohup python kp_run_eval.py -config config/test/config-rnn-keyphrase.yml -data_dir data/keyphrase/meng17/ -ckpt_dir models/keyphrase/1st/ -output_dir output/keyphrase/1st/ -testsets krapivin -batch_size 64 > output/keyphrase/kp_run_eval-krapivin.log &
111278

nohup python kp_run_eval.py -config config/test/config-rnn-keyphrase.yml -data_dir data/keyphrase/meng17/ -ckpt_dir models/keyphrase/1st/ -output_dir output/keyphrase/1st/ -testsets kp20k -batch_size 64 > output/keyphrase/kp_run_eval-kp20k.log &
