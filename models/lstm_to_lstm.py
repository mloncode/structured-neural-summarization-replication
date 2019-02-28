import torch
import torch.nn as nn


class Seq2Seq(nn.Module):
    def __init__(self, encoder, decoder, device, graph_encoder=None, graph=False):
        super().__init__()

        self.encoder = encoder
        self.graph_encoder = graph_encoder
        self.decoder = decoder
        self.device = device
        self.graph = graph

        assert encoder.hidden_size == decoder.hidden_size, "Hidden dimensions of encoder and decoder " \
                                                    "must be equal!"

    def forward(self, sequence, target, adj=None):
        batch_size = 1
        max_len = target.shape[0]
        target_vocab_size = self.decoder.output_size

        # tensor to store decoder outputs
        outputs = torch.zeros(max_len, batch_size, target_vocab_size).to(self.device)

        # last hidden state of the encoder is used as the initial hidden state of the decoder
        # hidden contains last hidden state of encoder
        # output contains the hidden states for all input elements
        encoder_output, hidden = self.encoder(sequence)

        if self.graph:
            # graph_hidden has shape [1, 1, hidden_size] and contains a graph representation
            n_nodes = adj.size(0)
            n_tokens = sequence.size(0)
            x = torch.zeros(n_nodes, encoder_output.size(2)).to(self.device)
            x[:n_tokens, :] = encoder_output.view(encoder_output.size(1), encoder_output.size(2))
            graph_hidden = self.graph_encoder(x=x, adj=adj)

            # TODO: Combine the graph representation with the seq_encoder final layer using mlp

            hidden = (graph_hidden.view(1, 1, graph_hidden.size(0)), hidden[1])

        # first input to the decoder is the <sos> tokens
        input = torch.tensor([[0]], device=self.device)

        for t in range(1, max_len):
            output, hidden = self.decoder(input, hidden, encoder_output)
            outputs[t] = output
            top1 = output.max(1)[1]
            input = top1

        return outputs

