#!/usr/bin/env bash
#SBATCH --cluster=gpu
#SBATCH --gres=gpu:1
#SBATCH --partition=titanx
#SBATCH --partition=gtx1080
#SBATCH --partition=v100
#SBATCH --account=hdaqing

#SBATCH --job-name=train-bart-kptimes-fewshot100
#SBATCH --output=slurm_output/train-bart-kptimes-fewshot100.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=32GB
#SBATCH --time=1-00:00:00 # 6 days walltime in dd-hh:mm format
#SBATCH --qos=long

# Load modules
#module restore
#module load cuda/10.0.130
#module load gcc/6.3.0
#module load python/anaconda3.6-5.2.0
#source activate py36
#module unload python/anaconda3.6-5.2.0

# GPU usage: --max-tokens=1536,--update-freq=16, bsz=110: k+MiB / 32480MiB
cd /zfs1/hdaqing/rum20/kp/fairseq-kpg/fairseq_cli/
export WANDB_NAME=bartFT_presabs_kptimes_fewshot100
export TOKENIZERS_PARALLELISM=false
cmd="python train.py /zfs1/hdaqing/rum20/kp/data/kp/json/kptimes_train100/train.json --dataset-type news --save-dir /zfs1/hdaqing/rum20/kp/fairseq-kpg/exps/kp_fewshot10k/bart_presabs_kptimes_fewshot100/ckpts --disable-validation --task keyphrasification --max-source-length 512 --max-target-length 128 --kp-concat-type pres_abs --arch bart_large --restore-file /zfs1/hdaqing/rum20/kp/data/kp/cache/bart.large/model.pt --bpe hf_pretrained_bpe --bpe-vocab /zfs1/hdaqing/rum20/kp/data/kp/hf_vocab/roberta-base-kp/vocab.json --bpe-merges /zfs1/hdaqing/rum20/kp/data/kp/hf_vocab/roberta-base-kp/merges.txt --dict-path /zfs1/hdaqing/rum20/kp/data/kp/hf_vocab/roberta-base-kp/dict.txt --bpe-dropout 0.0 --ddp-backend=no_c10d --criterion label_smoothed_cross_entropy --share-all-embeddings --layernorm-embedding --share-all-embeddings --share-decoder-input-output-embed --reset-optimizer --reset-dataloader --reset-meters --required-batch-size-multiple 1 --optimizer adam --adam-betas (0.9,0.999) --adam-eps 1e-08 --clip-norm 0.1 --lr 1e-5 --lr-scheduler polynomial_decay --label-smoothing 0.1 --dropout 0.1 --attention-dropout 0.1 --weight-decay 0.01 --log-format simple --log-interval 10 --fixed-validation-seed 7 --max-tokens 5760 --update-freq 10 --save-interval-updates 100 --warmup-updates 200 --total-num-update 2000 --num-workers 2 --find-unused-parameters --fp16 --ddp-backend=no_c10d --wandb-project transfer_kp_fewshot"

echo $CONFIG_PATH
echo $cmd

$cmd
