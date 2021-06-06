import torch
import torch.nn as nn
import itertools as it
from typing import Sequence

ACTIVATIONS = {"relu": nn.ReLU, "lrelu": nn.LeakyReLU}
POOLINGS = {"avg": nn.AvgPool2d, "max": nn.MaxPool2d}


class ConvClassifier(nn.Module):
    """
    A convolutional classifier model based on PyTorch nn.Modules.

    The architecture is:
    [(CONV -> ACT)*P -> POOL]*(N/P) -> (FC -> ACT)*M -> FC
    """

    def __init__(
        self,
        in_size,
        out_classes: int,
        channels: Sequence[int],
        pool_every: int,
        hidden_dims: Sequence[int],
        conv_params: dict = {},
        activation_type: str = "relu",
        activation_params: dict = {},
        pooling_type: str = "max",
        pooling_params: dict = {},
    ):
        """
        :param in_size: Size of input images, e.g. (C,H,W).
        :param out_classes: Number of classes to output in the final layer.
        :param channels: A list of of length N containing the number of
            (output) channels in each conv layer.
        :param pool_every: P, the number of conv layers before each max-pool.
        :param hidden_dims: List of of length M containing hidden dimensions of
            each Linear layer (not including the output layer).
        :param conv_params: Parameters for convolution layers.
        :param activation_type: Type of activation function; supports either 'relu' or
            'lrelu' for leaky relu.
        :param activation_params: Parameters passed to activation function.
        :param pooling_type: Type of pooling to apply; supports 'max' for max-pooling or
            'avg' for average pooling.
        :param pooling_params: Parameters passed to pooling layer.
        """
        super().__init__()
        assert channels and hidden_dims

        self.in_size = in_size
        self.out_classes = out_classes
        self.channels = channels
        self.pool_every = pool_every
        self.hidden_dims = hidden_dims
        self.conv_params = conv_params
        self.activation_type = activation_type
        self.activation_params = activation_params
        self.pooling_type = pooling_type
        self.pooling_params = pooling_params

        if activation_type not in ACTIVATIONS or pooling_type not in POOLINGS:
            raise ValueError("Unsupported activation or pooling type")

        self.feature_extractor = self._make_feature_extractor()
        self.classifier = self._make_classifier()

    def _make_feature_extractor(self):
        in_channels, in_h, in_w, = tuple(self.in_size) # 3,100,100

        layers = []
        # TODO: Create the feature extractor part of the model:
        #  [(CONV -> ACT)*P -> POOL]*(N/P)
        #  Apply activation function after each conv, using the activation type and
        #  parameters.
        #  Apply pooling to reduce dimensions after every P convolutions, using the
        #  pooling type and pooling parameters.
        #  Note: If N is not divisible by P, then N mod P additional
        #  CONV->ACTs should exist at the end, without a POOL after them.
        # ====== YOUR CODE: ======
        self.pools_num = 0
        self.features_num = 1
        
        filters_lst = [in_channels] + self.channels
 
        # convolution parameters
        conv_kernel  = self.conv_params["kernel_size"]
        conv_stride =  1 if "stride" not in self.conv_params else self.conv_params["stride"]
        conv_padding =  0 if "padding" not in self.conv_params else self.conv_params["padding"]
        conv_dilation  = 1 if "dilation" not in self.conv_params else self.conv_params["dilation"]
        #pooling parameters
        pool_kernel = self.pooling_params["kernel_size"]
        pool_stride =  self.pooling_params["kernel_size"] if "stride" not in self.pooling_params else self.pooling_params["stride"]

        pool_padding =  0 if "padding" not in self.pooling_params else self.pooling_params["padding"]
        pool_dilation =  1 if "dilation" not in self.pooling_params else self.pooling_params["dilation"]

        
        for idx in range(1, len(filters_lst)):
            in_channels = filters_lst[idx-1] #3
            out_channels = filters_lst[idx] #32
            
            layers.append(nn.Conv2d(in_channels=in_channels, out_channels=out_channels, kernel_size=conv_kernel, stride=conv_stride, padding=conv_padding, dilation=conv_dilation))
            #update features size after conv
            in_h = int(((in_h +2*conv_padding)-conv_dilation*(conv_kernel-1)-1)/conv_stride)+1
            in_w = int(((in_w +2*conv_padding)-conv_dilation*(conv_kernel-1)-1)/conv_stride)+1

            if self.activation_type == 'relu':
                layers.append(ACTIVATIONS[str(self.activation_type)]())
            elif self.activation_type == 'lrelu':
                layers.append(ACTIVATIONS[str(self.activation_type)](negative_slope=self.activation_params["negative_slope"]))
            
            #performing pooling once in pool_every conv layers
            if idx % self.pool_every == 0:
                if self.pooling_type == 'max':
                    layers.append(POOLINGS[str(self.pooling_type)](kernel_size=pool_kernel,stride=pool_stride,padding=pool_padding,dilation=pool_dilation))
                elif self.pooling_type == 'avg':
                    layers.append(POOLINGS[str(self.pooling_type)](kernel_size=pool_kernel,stride=pool_stride,padding=pool_padding))
                #update features size after pooling
                in_h = int(((in_h +2*pool_padding)-pool_dilation*(pool_kernel-1)-1)/pool_stride)+1
                in_w = int(((in_w +2*pool_padding)-pool_dilation*(pool_kernel-1)-1)/pool_stride)+1
                self.pools_num += 1
                
        self.features_num = self.channels[-1]*in_h*in_w
        # ========================
        seq = nn.Sequential(*layers)
        return seq

    def _n_features(self) -> int:
        """
        Calculates the number of extracted features going into the the classifier part.
        :return: Number of features.
        """
        # Make sure to not mess up the random state.
        rng_state = torch.get_rng_state()
        try:
            # ====== YOUR CODE: ======
            return self.features_num
            # ========================
        finally:
            torch.set_rng_state(rng_state)

    def _make_classifier(self):
        layers = []

        # Discover the number of features after the CNN part.
        n_features = self._n_features()

        # TODO: Create the classifier part of the model:
        #  (FC -> ACT)*M -> Linear
        #  The last Linear layer should have an output dim of out_classes.
        # ====== YOUR CODE: ======
        input_dimension = n_features
        for hidden in range(len(self.hidden_dims)):
            layers.append(nn.Linear(input_dimension, self.hidden_dims[hidden]))
            if self.activation_type == 'relu':
                layers.append(ACTIVATIONS[str(self.activation_type)]())
            elif  self.activation_type == 'lrelu':
                if self.activation_params:
                    layers.append(ACTIVATIONS[str(self.activation_type)](negative_slope=self.activation_params["negative_slope"]))
                else:
                    layers.append(ACTIVATIONS[str(self.activation_type)]())
            input_dimension = self.hidden_dims[hidden]
        layers.append(nn.Linear(input_dimension, self.out_classes))

        # ========================

        seq = nn.Sequential(*layers)
        return seq

    def forward(self, x):
        # TODO: Implement the forward pass.
        #  Extract features from the input, run the classifier on them and
        #  return class scores.
        # ====== YOUR CODE: ======
        extracted_features = self.feature_extractor(x)
        extracted_features = extracted_features.view(extracted_features.size(0), -1)
        out = self.classifier(extracted_features)
        # ========================
        return out


class ResidualBlock(nn.Module):
    """
    A general purpose residual block.
    """

    def __init__(
        self,
        in_channels: int,
        channels: Sequence[int],
        kernel_sizes: Sequence[int],
        batchnorm: bool = False,
        dropout: float = 0.0,
        activation_type: str = "relu",
        activation_params: dict = {},
        **kwargs,
    ):
        """
        :param in_channels: Number of input channels to the first convolution.
        :param channels: List of number of output channels for each
            convolution in the block. The length determines the number of
            convolutions.
        :param kernel_sizes: List of kernel sizes (spatial). Length should
            be the same as channels. Values should be odd numbers.
        :param batchnorm: True/False whether to apply BatchNorm between
            convolutions.
        :param dropout: Amount (p) of Dropout to apply between convolutions.
            Zero means don't apply dropout.
        :param activation_type: Type of activation function; supports either 'relu' or
            'lrelu' for leaky relu.
        :param activation_params: Parameters passed to activation function.
        """
        super().__init__()
        assert channels and kernel_sizes
        assert len(channels) == len(kernel_sizes)
        assert all(map(lambda x: x % 2 == 1, kernel_sizes))

        if activation_type not in ACTIVATIONS:
            raise ValueError("Unsupported activation type")

        self.main_path, self.shortcut_path = None, None

        # TODO: Implement a generic residual block.
        #  Use the given arguments to create two nn.Sequentials:
        #  - main_path, which should contain the convolution, dropout,
        #    batchnorm, relu sequences (in this order).
        #    Should end with a final conv as in the diagram.
        #  - shortcut_path which should represent the skip-connection and
        #    may contain a 1x1 conv.
        #  Notes:
        #  - Use convolutions which preserve the spatial extent of the input.
        #  - Use bias in the main_path conv layers, and no bias in the skips.
        #  - For simplicity of implementation, assume kernel sizes are odd.
        #  - Don't create layers which you don't use! This will prevent
        #    correct comparison in the test.
        # ====== YOUR CODE: ======
        main = []
        tmp_in_channels = in_channels
        for i, ch in enumerate(channels):
            
            main.append(nn.Conv2d(in_channels=tmp_in_channels, out_channels=ch, kernel_size=kernel_sizes[i], bias=True, padding=int(kernel_sizes[i]/2))) #1
            tmp_in_channels = ch
            
            if i == (len(channels) - 1):
                break
            
            main.append(nn.Dropout2d(p=dropout))#2
            
            if batchnorm:
                main.append(nn.BatchNorm2d(ch))#3
                
            if activation_type == 'relu': #4
                main.append(ACTIVATIONS[str(activation_type)]())
            elif activation_type == 'lrelu':
                if activation_params:
                    main.append(ACTIVATIONS[str(activation_type)](negative_slope=activation_params["negative_slope"]))
                else:
                    main.append(ACTIVATIONS[str(activation_type)]())
                
        self.main_path = nn.Sequential(*main)

        if (tmp_in_channels != in_channels):
            self.shortcut_path =  nn.Sequential(nn.Conv2d(in_channels=in_channels, out_channels=tmp_in_channels, kernel_size=1, bias=False))
        else:
            self.shortcut_path = nn.Sequential()
                
        # ========================

    def forward(self, x):
        out = self.main_path(x)
        out += self.shortcut_path(x)
        out = torch.relu(out)
        return out


class ResidualBottleneckBlock(ResidualBlock):
    """
    A residual bottleneck block.
    """

    def __init__(
        self,
        in_out_channels: int,
        inner_channels: Sequence[int],
        inner_kernel_sizes: Sequence[int],
        **kwargs,
    ):
        """
        :param in_out_channels: Number of input and output channels of the block.
            The first conv in this block will project from this number, and the
            last conv will project back to this number of channel.
        :param inner_channels: List of number of output channels for each internal
            convolution in the block (i.e. not the outer projections)
            The length determines the number of convolutions.
        :param inner_kernel_sizes: List of kernel sizes (spatial) for the internal
            convolutions in the block. Length should be the same as inner_channels.
            Values should be odd numbers.
        :param kwargs: Any additional arguments supported by ResidualBlock.
        """
        # ====== YOUR CODE: ======
        b_channels = [inner_channels[0]] + inner_channels + [in_out_channels]
        b_kernel_sizes = [1] + inner_kernel_sizes + [1]
        batchnorm = False if "batchnorm" not in kwargs else kwargs["batchnorm"]
        dropout = 0.0 if "dropout" not in kwargs else kwargs["dropout"]
        activation_type = "relu" if "activation_type" not in kwargs else kwargs["activation_type"]
        activation_params = {} if "activation_params" not in kwargs else kwargs["activation_params"]

        super().__init__(in_channels=in_out_channels,
        channels=b_channels,
        kernel_sizes=b_kernel_sizes,
        batchnorm=batchnorm,
        dropout=dropout,
        activation_type=activation_type,
        activation_params=activation_params)
        # ========================


class ResNetClassifier(ConvClassifier):
    def __init__(
        self,
        in_size,
        out_classes,
        channels,
        pool_every,
        hidden_dims,
        batchnorm=False,
        dropout=0.0,
        **kwargs,
    ):
        """
        See arguments of ConvClassifier & ResidualBlock.
        """
        self.batchnorm = batchnorm
        self.dropout = dropout
        super().__init__(
            in_size, out_classes, channels, pool_every, hidden_dims, **kwargs
        )

    def _make_feature_extractor(self):
        in_channels, in_h, in_w, = tuple(self.in_size)

        layers = []
        # TODO: Create the feature extractor part of the model:
        #  [-> (CONV -> ACT)*P -> POOL]*(N/P)
        #   \------- SKIP ------/
        #  For the ResidualBlocks, use only dimension-preserving 3x3 convolutions.
        #  Apply Pooling to reduce dimensions after every P convolutions.
        #  Notes:
        #  - If N is not divisible by P, then N mod P additional
        #    CONV->ACT (with a skip over them) should exist at the end,
        #    without a POOL after them.
        #  - Use your own ResidualBlock implementation.
        # ====== YOUR CODE: ======
        self.pools_num = 0
        self.features_num = 1

        in_channels, in_h, in_w, = tuple(self.in_size) 
        #pooling parameters
        pool_kernel = self.pooling_params["kernel_size"]
        pool_stride =  self.pooling_params["kernel_size"] if "stride" not in self.pooling_params else self.pooling_params["stride"]
        pool_padding =  0 if "padding" not in self.pooling_params else self.pooling_params["padding"]
        pool_dilation =  1 if "dilation" not in self.pooling_params else self.pooling_params["dilation"]
        
        channels_length = len(self.channels)
        remainder = channels_length % self.pool_every
        curr_channels = in_channels
        
        for index in range(int(channels_length / self.pool_every)):
            start_index = self.pool_every * index
            end_index = self.pool_every * (index + 1)
            
            #ResidualBlock: [conv->drop->batch->act]*p
            layers.append(ResidualBlock(in_channels= curr_channels, channels=self.channels[start_index : end_index], kernel_sizes=[3]*self.pool_every, batchnorm=self.batchnorm, dropout=self.dropout))
            # no need to update the dimensions - ResidualBlock saves dimensions
            
            #pooling 
            if self.pooling_type == 'max':
                layers.append(POOLINGS[str(self.pooling_type)](kernel_size=pool_kernel,stride=pool_stride,padding=pool_padding,dilation=pool_dilation))
            elif self.pooling_type == 'avg':
                layers.append(POOLINGS[str(self.pooling_type)](kernel_size=pool_kernel,stride=pool_stride,padding=pool_padding))
            
            #update features size after pooling
            in_h = int(((in_h +2*pool_padding)-pool_dilation*(pool_kernel-1)-1)/pool_stride)+1
            in_w = int(((in_w +2*pool_padding)-pool_dilation*(pool_kernel-1)-1)/pool_stride)+1
            self.pools_num += 1
            
            curr_channels = self.channels[end_index - 1]
        if remainder != 0:
            layers.append(ResidualBlock(in_channels= curr_channels, channels=self.channels[channels_length-remainder:], kernel_sizes=[3]*remainder, batchnorm=self.batchnorm, dropout=self.dropout))
        self.features_num = self.channels[-1]*in_h*in_w
        # ========================
        seq = nn.Sequential(*layers)
        return seq


class YourCodeNet(ConvClassifier):
    def __init__(self, *args, **kwargs):
        """
        See ConvClassifier.__init__
        """
        super().__init__(*args, **kwargs)

        # TODO: Add any additional initialization as needed.
        # ====== YOUR CODE: ======
        self.feature_extractor = self._make_feature_extractor()
#         self.classifier = nn.Linear(self.features_num, self.out_classes)
        self.classifier = self._make_classifier()
        self.dropout = nn.Dropout(0.1)
        # ========================

    # TODO: Change whatever you want about the ConvClassifier to try to
    #  improve it's results on CIFAR-10.
    #  For example, add batchnorm, dropout, skip connections, change conv
    #  filter sizes etc.
    # ====== YOUR CODE: ======
    def _make_feature_extractor(self):
        import random
        in_channels, in_h, in_w, = tuple(self.in_size) # 3,100,100

        layers = []

        self.pools_num = 0
        self.features_num = 1
     
        pool_kernel = 2
        pool_stride =  2
        pool_padding = 0
        pool_dilation=1

        in_channels, in_h, in_w, = tuple(self.in_size) 
        
        channels_length = len(self.channels)
        remainder = channels_length % self.pool_every
        curr_channels = in_channels
        last = int(channels_length / self.pool_every)
        for index in range(last):
            start_index = self.pool_every * index
            end_index = self.pool_every * (index + 1)
            
            # ResidualBlock saves dimensions: [conv->drop->batch->act]*p
            layers.append(ResidualBlock(in_channels= curr_channels, channels=self.channels[start_index : end_index], kernel_sizes=[3]*self.pool_every, batchnorm="true", dropout=0.0))

            #pooling
            if (index == last-1):
                layers.append(nn.MaxPool2d(kernel_size=pool_kernel, stride=pool_stride, padding=pool_padding, dilation=pool_dilation))
                layers.append(nn.Dropout2d(p=0.1))
                
                self.pools_num += 1

                #update features size after pooling
                in_h = int(((in_h +2*pool_padding)-pool_dilation*(pool_kernel-1)-1)/pool_stride)+1
                in_w = int(((in_w +2*pool_padding)-pool_dilation*(pool_kernel-1)-1)/pool_stride)+1
            
            curr_channels = self.channels[end_index - 1]
        if remainder != 0:
            layers.append(ResidualBlock(in_channels= curr_channels, channels=self.channels[channels_length-remainder:], kernel_sizes=[3]*remainder, batchnorm="true", dropout=0.0))
        
        #updating parameters
        self.features_num = self.channels[-1]*in_h*in_w
        
        seq = nn.Sequential(*layers)
        return seq
    


    
    
    