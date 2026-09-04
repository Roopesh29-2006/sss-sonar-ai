import torch
import torch.nn as nn
import torch.nn.functional as F
# pyrefly: ignore [missing-import]
from torchvision.models import resnet18

class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)

class DecoderBlock(nn.Module):
    def __init__(self, in_channels: int, skip_channels: int, out_channels: int):
        super().__init__()
        self.conv = ConvBlock(in_channels + skip_channels, out_channels)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        # Dynamically interpolate x to match skip connection spatial dimensions (H_skip, W_skip)
        x = F.interpolate(x, size=(skip.size(2), skip.size(3)), mode='bilinear', align_corners=False)
        x = torch.cat([x, skip], dim=1)
        return self.conv(x)

class SSLUNet(nn.Module):
    """
    Exact PyTorch SSL-UNet Architecture matching best_ssl_unet_accuracy.pth
    ResNet18 Backbone Encoder (1-channel input) + UNet Decoder
    """
    def __init__(self, in_channels: int = 1, num_classes: int = 1):
        super().__init__()
        base_resnet = resnet18(weights=None)
        
        self.encoder = base_resnet
        # Replace first conv to accept 1-channel sonar input
        self.encoder.conv1 = nn.Conv2d(
            in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False
        )
        # Replace classification head with no-ops (we use encoder features only)
        self.encoder.fc = nn.Identity()
        self.encoder.avgpool = nn.Identity()

        self.dec4 = DecoderBlock(in_channels=512, skip_channels=256, out_channels=256)
        self.dec3 = DecoderBlock(in_channels=256, skip_channels=128, out_channels=128)
        self.dec2 = DecoderBlock(in_channels=128, skip_channels=64, out_channels=64)

        self.final_conv = nn.Sequential(
            nn.Conv2d(64, 32, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, num_classes, kernel_size=1)
        )

    def extract_encoder_features(self, x: torch.Tensor) -> torch.Tensor:
        """Return the deepest real SSL encoder map before the U-Net decoder."""
        x0 = self.encoder.conv1(x)
        x0 = self.encoder.bn1(x0)
        x0 = self.encoder.relu(x0)
        e1 = self.encoder.layer1(self.encoder.maxpool(x0))
        e2 = self.encoder.layer2(e1)
        e3 = self.encoder.layer3(e2)
        return self.encoder.layer4(e3)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        orig_shape = (x.size(2), x.size(3))

        x0 = self.encoder.conv1(x)
        x0 = self.encoder.bn1(x0)
        x0 = self.encoder.relu(x0)
        e1 = self.encoder.layer1(self.encoder.maxpool(x0))
        e2 = self.encoder.layer2(e1)
        e3 = self.encoder.layer3(e2)
        e4 = self.encoder.layer4(e3)

        d4 = self.dec4(e4, e3)  # 512 + 256 -> 256
        d3 = self.dec3(d4, e2)  # 256 + 128 -> 128
        d2 = self.dec2(d3, e1)  # 128 + 64 -> 64

        out = F.interpolate(d2, size=orig_shape, mode='bilinear', align_corners=False)
        out = self.final_conv(out)
        return out
