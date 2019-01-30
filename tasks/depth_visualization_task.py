"""
    Defines tasks for evaluation
"""
from tasks.task import Task
from datasets.get import get_dataset
import torch
from misc_utils import gdb


class DepthVisualizationTask(Task):
    def __init__(self, model, epoch, args):
        super(DepthVisualizationTask, self).__init__()
        self.num_videos = 5

    @classmethod
    def run(cls, model, criterion, epoch, args):
        task = cls(model, epoch, args)
        train_loader, val_loader = get_dataset(args, splits=('train', 'val'), dataset=args.dataset)
        model.eval()
        task.visualize_all(train_loader, model, epoch, args, 'train')
        task.visualize_all(val_loader, model, epoch, args, 'val')
        return {'depth_visualization_task': args.cache}

    def visualize_all(self, loader, model, epoch, args, split):
        for i, (inputs, target, meta) in enumerate(loader):
            if i >= self.num_videos:
                break
            if not args.cpu:
                inputs = inputs.cuda()
                target = target.cuda(async=True)
            tgt_img, ref_imgs, intrinsics, intrinsics_inv, depth, explainability_mask, pose = model(inputs, meta)

            # prepare images
            original = tgt_img[0]
            original *= torch.Tensor([0.229, 0.224, 0.225])[:, None, None].to(original.device)
            original += torch.Tensor([0.485, 0.456, 0.406])[:, None, None].to(original.device)
            original = original.permute(1, 2, 0)

            # prepare depth
            output = depth[0].clone()
            output = output / (1e-6 + output.max())
            output = output.clamp(0, 1)
            output = output.repeat(3, 1, 1)
            output = output.permute(1, 2, 0)

            # debug
            print('depth min: {} depth max: {} depth mean: {} depth median: {}'.format(depth[0].min(), depth[0].max(), depth[0].mean(), depth[0].median()))

            # prepare depth not normalized
            raw = depth[0].clone()
            raw = raw / 10
            raw = raw.clamp(0, 1)
            raw = raw.repeat(3, 1, 1)
            raw = raw.permute(1, 2, 0)

            # prepare depth median normalized
            median = depth[0].clone()
            median = median / (1e-6 + 2*median.median())
            median = median.clamp(0, 1)
            median = median.repeat(3, 1, 1)
            median = median.permute(1, 2, 0)

            # prepare disparity
            disp = depth[0].clone()
            disp = 1 / disp
            disp = disp / (1e-6 + disp.max())
            disp = disp.clamp(0, 1)
            disp = disp.repeat(3, 1, 1)
            disp = disp.permute(1, 2, 0)

            # prepare depth full normalize
            normed = depth[0].clone()
            normed = normed - normed.min()
            normed = normed / (1e-6 + normed.max())
            normed = normed.clamp(0, 1)
            normed = normed.repeat(3, 1, 1)
            normed = normed.permute(1, 2, 0)

            # save video
            name = '{}_{:03d}_{}_{}'.format(split, epoch, meta[0]['id'], meta[0]['time'])
            gdb.arrtoim(original.cpu().numpy().copy()).save('{}/{}_original.png'.format(args.cache, name))
            gdb.arrtoim(output.cpu().numpy().copy()).save('{}/{}_output.png'.format(args.cache, name))
            gdb.arrtoim(raw.cpu().numpy().copy()).save('{}/{}_raw.png'.format(args.cache, name))
            gdb.arrtoim(median.cpu().numpy().copy()).save('{}/{}_median.png'.format(args.cache, name))
            gdb.arrtoim(disp.cpu().numpy().copy()).save('{}/{}_disp.png'.format(args.cache, name))
            gdb.arrtoim(normed.cpu().numpy().copy()).save('{}/{}_normed.png'.format(args.cache, name))
            combined = torch.cat((original.cpu(), output.cpu(), raw.cpu(), median.cpu(), disp.cpu(), normed.cpu()), 1)
            gdb.arrtoim(combined.cpu().numpy().copy()).save('{}/{}_combined.png'.format(args.cache, name))

            print('Visualization: [{0}/{1}]'.format(i, self.num_videos))