import torch.nn as nn

from models.BasicModule import BasicModule

__all__ = ['ResNet50', 'ResNet101', 'ResNet152']


def Conv1(in_planes, places, stride=2):
    return nn.Sequential(
        nn.Conv2d(in_channels=in_planes, out_channels=places, kernel_size=8, stride=stride, padding=3, bias=False),
        nn.BatchNorm2d(places),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(kernel_size=4, stride=2, padding=1),
        nn.Conv2d(in_channels=places, out_channels=places, kernel_size=3, stride=2, padding=0, bias=False),
        nn.BatchNorm2d(places),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(kernel_size=3, stride=2, padding=0)
    )


class Bottleneck(nn.Module):
    def __init__(self, in_places, places, stride=1, downsampling=False, expansion=4):
        super(Bottleneck, self).__init__()
        self.expansion = expansion
        self.downsampling = downsampling

        self.bottleneck = nn.Sequential(
            nn.Conv2d(in_channels=in_places, out_channels=places, kernel_size=1, stride=1, bias=False),
            nn.BatchNorm2d(places),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels=places, out_channels=places, kernel_size=3, stride=stride, padding=1, bias=False),
            nn.BatchNorm2d(places),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels=places, out_channels=places * self.expansion, kernel_size=1, stride=1, bias=False),
            nn.BatchNorm2d(places * self.expansion),
        )

        if self.downsampling:
            self.downsample = nn.Sequential(
                nn.Conv2d(in_channels=in_places, out_channels=places * self.expansion, kernel_size=1, stride=stride,
                          bias=False),
                nn.BatchNorm2d(places * self.expansion)
            )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        residual = x
        out = self.bottleneck(x)

        if self.downsampling:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)
        return out


class ResNet(BasicModule):
    def __init__(self, blocks, num_classes=1000, expansion=4, input_channel=3):
        super(ResNet, self).__init__()
        self.model_name = 'resnet'
        self.expansion = expansion

        self.conv1 = Conv1(in_planes=input_channel, places=64)

        self.layer1 = self.make_layer(input_channel=64, output_channel=64, block=blocks[0], stride=1)
        self.layer2 = self.make_layer(input_channel=256, output_channel=128, block=blocks[1], stride=2)
        self.layer3 = self.make_layer(input_channel=512, output_channel=256, block=blocks[2], stride=2)
        self.layer4 = self.make_layer(input_channel=1024, output_channel=512, block=blocks[3], stride=2)

        self.avgpool = nn.AvgPool2d(10, stride=1)
        self.classifier = nn.Sequential(
            nn.Linear(2048, 1024),
            nn.Linear(1024, 512),
            nn.Linear(512, 256),
            nn.Linear(256, 128),
            nn.Linear(128, 64),
            nn.Linear(64, 32),
            nn.Linear(32, num_classes)
        )

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def make_layer(self, input_channel, output_channel, block, stride):
        layers = []
        layers.append(Bottleneck(input_channel, output_channel, stride, downsampling=True))
        for i in range(1, block):
            layers.append(Bottleneck(output_channel * self.expansion, output_channel))

        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv1(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x


def ResNet50(num_classes=2, expansion=4, input_channel=1):
    return ResNet([3, 4, 6, 3], num_classes, expansion, input_channel)


def ResNet101(num_classes=2, expansion=4, input_channel=1):
    return ResNet([3, 4, 23, 3], num_classes, expansion, input_channel)


def ResNet152(num_classes=2, expansion=4, input_channel=1):
    return ResNet([3, 8, 36, 3], num_classes, expansion, input_channel)