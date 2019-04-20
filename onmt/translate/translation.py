""" Translation main class """
from __future__ import unicode_literals, print_function

import torch

from onmt.inputters import KeyphraseDataset
from onmt.inputters.text_dataset import TextMultiField


class TranslationBuilder(object):
    """
    Build a word-based translation from the batch output
    of translator and the underlying dictionaries.

    Replacement based on "Addressing the Rare Word
    Problem in Neural Machine Translation" :cite:`Luong2015b`

    Args:
       data (onmt.inputters.Dataset): Data.
       fields (List[Tuple[str, torchtext.data.Field]]): data fields
       n_best (int): number of translations produced
       replace_unk (bool): replace unknown words using attention
       has_tgt (bool): will the batch have gold targets
    """

    def __init__(self, data, fields, n_best=1, replace_unk=False,
                 has_tgt=False):
        self.data = data
        self.fields = fields
        self._has_text_src = isinstance(
            dict(self.fields)["src"], TextMultiField)
        self.n_best = n_best
        self.replace_unk = replace_unk
        self.has_tgt = has_tgt

    def _build_target_tokens(self, src, src_vocab, src_raw, pred, attn):
        tgt_field = dict(self.fields)["tgt"].base_field
        vocab = tgt_field.vocab
        tokens = []

        for tok in pred:
            if tok < len(vocab):
                tokens.append(vocab.itos[tok])
            else:
                tokens.append(src_vocab.itos[tok - len(vocab)])
            if tokens[-1] == tgt_field.eos_token:
                tokens = tokens[:-1]
                break
        if self.replace_unk and attn is not None and src is not None:
            for i in range(len(tokens)):
                if tokens[i] == tgt_field.unk_token:
                    _, max_index = attn[i].max(0)
                    tokens[i] = src_raw[max_index.item()]
        return tokens

    def from_batch(self, translation_batch):
        batch = translation_batch["batch"]
        assert(len(translation_batch["gold_score"]) ==
               len(translation_batch["predictions"]))
        batch_size = batch.batch_size

        preds, pred_score, attn, gold_score, indices = list(zip(
            *sorted(zip(translation_batch["predictions"],
                        translation_batch["scores"],
                        translation_batch["attention"],
                        translation_batch["gold_score"],
                        batch.indices.data),
                    key=lambda x: x[-1])))

        # Sorting
        inds, perm = torch.sort(batch.indices)
        if self._has_text_src:
            src = batch.src[0][:, :, 0].index_select(1, perm)
        else:
            src = None

        # if only one tgt: batch.tgt.dim=[max_seq_len, batch_size, 1]
        # if multiple tgts: batch.tgt.dim=[max_seq_len, batch_size, max_seq_num, 1]
        if self.has_tgt:
            if len(batch.tgt.size()) == 3:
                tgt = batch.tgt[:, :, 0].index_select(1, perm)
            else:
                tgt = batch.tgt[:, :, :, 0].index_select(1, perm)
        else:
            tgt = None

        translations = []
        for b in range(batch_size):
            if self._has_text_src:
                src_vocab = self.data.src_vocabs[inds[b]] \
                    if self.data.src_vocabs else None
                src_raw = self.data.examples[inds[b]].src[0]
            else:
                src_vocab = None
                src_raw = None
            # @memray: len(preds[b]) can be smaller than n_best
            pred_sents = [self._build_target_tokens(
                src[:, b] if src is not None else None,
                src_vocab, src_raw,
                preds[b][n], attn[b][n])
                for n in range(min(self.n_best, len(preds[b])))]
            gold_sent = None
            if tgt is not None:
                if tgt.dim() == 2:
                    gold_sent = self._build_target_tokens(
                        src[:, b] if src is not None else None,
                        src_vocab, src_raw,
                        tgt[1:, b] if tgt is not None else None, None)
                else:
                    gold_sent = [self._build_target_tokens(
                        src[:, b] if src is not None else None,
                        src_vocab, src_raw,
                        tgt[1:, b, n], None)
                        for n in range(tgt.size(2))]
                    gold_sent = [s for s in gold_sent if all([t != '<blank>' for t in s])]
            translation = Translation(
                src[:, b] if src is not None else None,
                src_raw, pred_sents, attn[b], pred_score[b],
                gold_sent, gold_score[b], preds[b]
            )
            translations.append(translation)

        return translations


class Translation(object):
    """Container for a translated sentence.

    Attributes:
        src (LongTensor): Source word IDs.
        src_raw (List[str]): Raw source words.
        pred_sents (List[List[str]]): Words from the n-best translations.
        pred_scores (List[List[float]]): Log-probs of n-best translations.
        attns (List[FloatTensor]) : Attention distribution for each
            translation.
        gold_sent (List[str]): Words from gold translation.
        gold_score (List[float]): Log-prob of gold translation.
        preds (List[LongTensor]): Original indices of predicted words, added by # @memray
    """

    __slots__ = ["src", "src_raw", "pred_sents", "attns", "pred_scores",
                 "gold_sent", "gold_score", "preds", "copied_flags"]

    def __init__(self, src, src_raw, pred_sents,
                 attn, pred_scores, tgt_sent, gold_score, preds, copied_flags=None):
        self.src = src
        self.src_raw = src_raw
        self.pred_sents = pred_sents
        self.attns = attn
        self.pred_scores = pred_scores
        self.gold_sent = tgt_sent
        self.gold_score = gold_score
        self.preds = preds
        self.copied_flags = copied_flags

    def log(self, sent_number):
        """
        Log translation.
        """
        msg = ['\nSENT {}: {}\n'.format(sent_number, self.src_raw)]

        best_pred = self.pred_sents[0]
        best_score = self.pred_scores[0]
        pred_sent = ' '.join(best_pred)
        msg.append('PRED {}: {}\n'.format(sent_number, pred_sent))
        msg.append("PRED SCORE: {:.4f}\n".format(best_score))

        if self.gold_sent is not None:
            tgt_sent = ' '.join(self.gold_sent)
            msg.append('GOLD {}: {}\n'.format(sent_number, tgt_sent))
            msg.append(("GOLD SCORE: {:.4f}\n".format(self.gold_score)))
        if len(self.pred_sents) > 1:
            msg.append('\nBEST HYP:\n')
            for score, sent in zip(self.pred_scores, self.pred_sents):
                msg.append("[{:.4f}] {}\n".format(score, sent))

        return "".join(msg)

    def __dict__(self):
        """
        Added by @memray to facilitate exporting json
        :return:
        """
        ret = {slot: getattr(self, slot) for slot in self.__slots__}
        if torch.cuda.is_available():
            ret['src'] = ret['src'].cpu().numpy().tolist()
            ret['pred_scores'] = [t.cpu().numpy().tolist() for t in ret['pred_scores']]
            ret['preds'] = [t.cpu().numpy().tolist() for t in ret['preds']]
            if self.copied_flags:
                ret['copied_flags'] = [t.cpu().numpy().tolist() for t in ret['copied_flags']]
        else:
            ret['src'] = ret['src'].numpy().tolist()
            ret['pred_scores'] = [t.numpy().tolist() for t in ret['pred_scores']]
            ret['preds'] = [t.numpy().tolist() for t in ret['preds']]
            if self.copied_flags:
                ret['copied_flags'] = [t.numpy().tolist() for t in ret['copied_flags']]

        return ret


    def log_kp(self, sent_number):
        """
        Log keyphrase generation.
        """

        msg = ['\nSENT {}: {}\n'.format(sent_number, self.src_raw)]

        best_pred = self.pred_sents[0]
        best_score = self.pred_scores[0]
        pred_sent = ' '.join(best_pred)
        msg.append('PRED {}: {}\n'.format(sent_number, pred_sent))
        msg.append("PRED SCORE: {:.4f}\n".format(best_score))

        if self.gold_sent is not None:
            tgt_sent = '\n\t'.join([' '.join(tgt) for tgt in self.gold_sent])
            msg.append('GOLD {}: \n\t{}\n'.format(sent_number, tgt_sent))
            msg.append(("GOLD SCORE: {:.4f}\n".format(self.gold_score)))
        if len(self.pred_sents) > 1:
            msg.append('\nBEST HYP:\n')
            for t_id, (score, sent, pred, copied_flag) in enumerate(zip(self.pred_scores, self.pred_sents, self.preds, self.copied_flags)):
                tmp_pred = pred.cpu().numpy().tolist() if torch.cuda.is_available() else pred.numpy().tolist()
                msg.append("[{}][{:.4f}] {} {} {}\n".format(t_id + 1, score, sent, tmp_pred, '[Copy!]' if any(copied_flag) else ''))

        return "".join(msg)

    def add_copied_flags(self, vocab_size):
        self.copied_flags = [pred.ge(vocab_size) for pred in self.preds]