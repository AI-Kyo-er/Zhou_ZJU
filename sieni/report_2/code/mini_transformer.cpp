#include <iostream>
#include <vector>
#include <random>
#include <cmath>
#include <chrono>

// Mini Transformer for fast gem5 simulation
// Much smaller dimensions to reduce simulation time

class MiniMatrix {
private:
    std::vector<float> data;
    int rows, cols;
    
public:
    MiniMatrix(int r, int c) : rows(r), cols(c), data(r * c, 0.0f) {}
    
    float& operator()(int i, int j) {
        return data[i * cols + j];
    }
    
    const float& operator()(int i, int j) const {
        return data[i * cols + j];
    }
    
    int getRows() const { return rows; }
    int getCols() const { return cols; }
    
    // Simple matrix multiplication (reduced complexity)
    MiniMatrix multiply(const MiniMatrix& other) const {
        MiniMatrix result(rows, other.cols);
        
        for (int i = 0; i < rows; i++) {
            for (int j = 0; j < other.cols; j++) {
                float sum = 0.0f;
                for (int k = 0; k < cols; k++) {
                    sum += (*this)(i, k) * other(k, j);
                }
                result(i, j) = sum;
            }
        }
        return result;
    }
    
    void randomize() {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_real_distribution<float> dis(-0.1f, 0.1f);
        
        for (auto& val : data) {
            val = dis(gen);
        }
    }
};

class MiniAttention {
private:
    int d_model;
    int num_heads;
    int d_k;
    
public:
    MiniAttention(int model_dim, int heads) 
        : d_model(model_dim), num_heads(heads), d_k(model_dim / heads) {}
    
    MiniMatrix forward(const MiniMatrix& input) {
        // Simplified attention calculation
        int seq_len = input.getRows();
        
        // Create simplified Q, K, V matrices
        MiniMatrix Q(seq_len, d_model);
        MiniMatrix K(seq_len, d_model);
        MiniMatrix V(seq_len, d_model);
        
        // Copy input as Q, K, V (simplified)
        for (int i = 0; i < seq_len; i++) {
            for (int j = 0; j < d_model; j++) {
                Q(i, j) = input(i, j) * 0.8f;
                K(i, j) = input(i, j) * 0.9f;
                V(i, j) = input(i, j) * 1.1f;
            }
        }
        
        // Simplified attention scores
        MiniMatrix scores(seq_len, seq_len);
        for (int i = 0; i < seq_len; i++) {
            for (int j = 0; j < seq_len; j++) {
                float score = 0.0f;
                for (int k = 0; k < d_model; k++) {
                    score += Q(i, k) * K(j, k);
                }
                scores(i, j) = score / sqrt(d_model);
            }
        }
        
        // Apply softmax (simplified)
        for (int i = 0; i < seq_len; i++) {
            float sum = 0.0f;
            for (int j = 0; j < seq_len; j++) {
                scores(i, j) = exp(scores(i, j));
                sum += scores(i, j);
            }
            for (int j = 0; j < seq_len; j++) {
                scores(i, j) /= sum;
            }
        }
        
        // Apply to values
        MiniMatrix output(seq_len, d_model);
        for (int i = 0; i < seq_len; i++) {
            for (int j = 0; j < d_model; j++) {
                float sum = 0.0f;
                for (int k = 0; k < seq_len; k++) {
                    sum += scores(i, k) * V(k, j);
                }
                output(i, j) = sum;
            }
        }
        
        return output;
    }
};

class MiniFeedForward {
private:
    int d_model;
    int d_ff;
    
public:
    MiniFeedForward(int model_dim, int ff_dim) 
        : d_model(model_dim), d_ff(ff_dim) {}
    
    MiniMatrix forward(const MiniMatrix& input) {
        int seq_len = input.getRows();
        
        // First layer: d_model -> d_ff
        MiniMatrix hidden(seq_len, d_ff);
        for (int i = 0; i < seq_len; i++) {
            for (int j = 0; j < d_ff; j++) {
                float sum = 0.0f;
                for (int k = 0; k < d_model; k++) {
                    sum += input(i, k) * 0.1f; // Simplified weights
                }
                hidden(i, j) = std::max(0.0f, sum); // ReLU
            }
        }
        
        // Second layer: d_ff -> d_model
        MiniMatrix output(seq_len, d_model);
        for (int i = 0; i < seq_len; i++) {
            for (int j = 0; j < d_model; j++) {
                float sum = 0.0f;
                for (int k = 0; k < d_ff; k++) {
                    sum += hidden(i, k) * 0.1f; // Simplified weights
                }
                output(i, j) = sum;
            }
        }
        
        return output;
    }
};

class MiniTransformerLayer {
private:
    MiniAttention attention;
    MiniFeedForward feedforward;
    
public:
    MiniTransformerLayer(int d_model, int num_heads, int d_ff)
        : attention(d_model, num_heads), feedforward(d_model, d_ff) {}
    
    MiniMatrix forward(const MiniMatrix& input) {
        // Self-attention with residual connection
        MiniMatrix attn_output = attention.forward(input);
        
        // Add residual connection
        MiniMatrix residual1(input.getRows(), input.getCols());
        for (int i = 0; i < input.getRows(); i++) {
            for (int j = 0; j < input.getCols(); j++) {
                residual1(i, j) = input(i, j) + attn_output(i, j);
            }
        }
        
        // Feed-forward with residual connection
        MiniMatrix ff_output = feedforward.forward(residual1);
        
        MiniMatrix output(input.getRows(), input.getCols());
        for (int i = 0; i < input.getRows(); i++) {
            for (int j = 0; j < input.getCols(); j++) {
                output(i, j) = residual1(i, j) + ff_output(i, j);
            }
        }
        
        return output;
    }
};

class MiniTransformer {
private:
    std::vector<MiniTransformerLayer> layers;
    int d_model;
    int num_heads;
    int d_ff;
    int num_layers;
    
public:
    MiniTransformer(int model_dim, int heads, int ff_dim, int layers_count)
        : d_model(model_dim), num_heads(heads), d_ff(ff_dim), num_layers(layers_count) {
        
        // Create layers
        for (int i = 0; i < num_layers; i++) {
            layers.emplace_back(d_model, num_heads, d_ff);
        }
    }
    
    MiniMatrix forward(const MiniMatrix& input) {
        MiniMatrix current = input;
        
        // Pass through each layer
        for (auto& layer : layers) {
            current = layer.forward(current);
        }
        
        return current;
    }
    
    void printStats() const {
        std::cout << "Mini Transformer Configuration:" << std::endl;
        std::cout << "  Model dimension: " << d_model << std::endl;
        std::cout << "  Number of heads: " << num_heads << std::endl;
        std::cout << "  Feed-forward dimension: " << d_ff << std::endl;
        std::cout << "  Number of layers: " << num_layers << std::endl;
    }
};

int main() {
    std::cout << "Starting Mini Transformer for gem5 Cache Analysis" << std::endl;
    
    // Much smaller configuration for faster simulation
    const int d_model = 32;     // Very small model dimension
    const int num_heads = 2;    // Few attention heads  
    const int d_ff = 64;        // Small feed-forward dimension
    const int num_layers = 2;   // Few layers
    const int seq_len = 8;      // Very short sequence
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    // Create mini transformer
    MiniTransformer transformer(d_model, num_heads, d_ff, num_layers);
    transformer.printStats();
    
    // Create small input
    MiniMatrix input(seq_len, d_model);
    input.randomize();
    
    std::cout << "Processing sequence of length " << seq_len << "..." << std::endl;
    
    // Forward pass
    MiniMatrix output = transformer.forward(input);
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    
    // Print results
    std::cout << "Forward pass completed!" << std::endl;
    std::cout << "Output shape: " << output.getRows() << "x" << output.getCols() << std::endl;
    std::cout << "Execution time: " << duration.count() << " ms" << std::endl;
    
    // Print some output values for verification
    std::cout << "Sample output values:" << std::endl;
    for (int i = 0; i < std::min(3, output.getRows()); i++) {
        for (int j = 0; j < std::min(4, output.getCols()); j++) {
            std::cout << output(i, j) << " ";
        }
        std::cout << std::endl;
    }
    
    std::cout << "Mini Transformer execution completed successfully!" << std::endl;
    return 0;
} 

/*
1. 先有 report， 框架.
2. pin-based simulator.
*/