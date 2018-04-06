import argparse
import matplotlib.pyplot as plt
import numpy as np
import time

import chainer
from chainercv.datasets import voc_bbox_label_names
from chainercv.links import FasterRCNNVGG16
from chainercv.links import SSD300
from chainercv.links import SSD512

from chainer_sort.models import SORTMultiObjectTracking
from chainer_sort.datasets.mot.mot_utils import get_sequence_map
from chainer_sort.datasets import MOTDataset
from chainer_sort.visualizations import vis_tracking_bbox


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--display', action='store_true')
    parser.add_argument(
        '--model', choices=('ssd300', 'ssd512', 'faster-rcnn-vgg16'),
        default='ssd512')
    parser.add_argument('--gpu', type=int, default=0)
    parser.add_argument(
        '--pretrained_model', choices=('voc0712', 'voc07'), default='voc0712')
    parser.add_argument('--sequence', '-s', default='c2-test')
    args = parser.parse_args()

    map_name, split = args.sequence.split('-')
    if split == 'test':
        split = 'val'
    sequences = get_sequence_map(split, map_name)

    if args.model == 'ssd300':
        detector = SSD300(
            n_fg_class=len(voc_bbox_label_names),
            pretrained_model=args.pretrained_model)
    elif args.model == 'ssd512':
        detector = SSD512(
            n_fg_class=len(voc_bbox_label_names),
            pretrained_model=args.pretrained_model)
    elif args.model == 'faster_rcnn_vgg16':
        detector = FasterRCNNVGG16(
            n_fg_class=len(voc_bbox_label_names),
            pretrained_model=args.pretrained_model)
    detector.use_preset('evaluate')
    detector.score_thresh = 0.5

    if args.gpu >= 0:
        chainer.cuda.get_device_from_id(args.gpu).use()
        detector.to_gpu()

    sort_label_names = ['person']

    if args.display:
        plt.ion()
        fig = plt.figure()

    for seq in sequences:
        if args.display:
            ax = fig.add_subplot(111, aspect='equal')

        dataset = MOTDataset(
            year='2015', split=split, sequence=seq)

        model = SORTMultiObjectTracking(
            detector, voc_bbox_label_names,
            sort_label_names)

        print('Sequence: {}'.format(seq))
        cycle_times = []
        for i in range(len(dataset)):
            img, _, _ = dataset[i]
            start_time = time.time()
            bboxes, labels, scores, inst_ids = model.predict([img])
            cycle_time = time.time() - start_time
            cycle_times.append(cycle_time)
            if args.display:
                bbox = bboxes[0]
                inst_id = inst_ids[0]
                label = labels[0]
                score = scores[0]
                vis_tracking_bbox(
                    img, bbox, inst_id, label, score,
                    label_names=voc_bbox_label_names, ax=ax)
                fig.canvas.flush_events()
                plt.draw()
                ax.cla()

        cycle_times = np.array(cycle_times)
        print('total time: {}'.format(np.sum(cycle_times)))
        print('average time: {}'.format(np.average(cycle_times)))


if __name__ == '__main__':
    main()
