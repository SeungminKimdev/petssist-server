import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import scipy.signal
from scipy.signal import find_peaks, stft
from scipy.ndimage import gaussian_filter1d
import math
import pywt

########## 전처리 관련
def get_bcg_respiration_signal(bcg: np.ndarray, SR: int) -> np.ndarray:
    bcg = bcg.flatten()
    filter_coeffs = scipy.signal.butter(5, 0.7, 'low', fs=SR)
    return scipy.signal.filtfilt(*filter_coeffs, bcg)

def get_bcg_heartrate_signal(bcg: np.ndarray, SR: float) -> np.ndarray:
    bcg = bcg.flatten()
    filter_coeffs = scipy.signal.butter(5, [5, 15], 'band', fs=SR)
    return scipy.signal.filtfilt(*filter_coeffs, bcg)

def normalize_signal_window(signal: np.ndarray, window_size: int = 70) -> np.ndarray:
    normalized_signal = np.zeros_like(signal)
    
    for i in range(len(signal)):
        start_index = max(0, i - window_size + 1)
        window = signal[start_index:i+1]
        min_val = np.min(window)
        max_val = np.max(window)
        if max_val != min_val:
            normalized_signal[i] = (signal[i] - min_val) / (max_val - min_val)
        else:
            normalized_signal[i] = 0.5
    return normalized_signal

def calculate_checked_values(signal: np.ndarray, window_size: int = 10, threshold: float = 0.75):
    checked_values = np.zeros_like(signal)
    max_min_diff = np.zeros_like(signal)
    upto = np.zeros_like(signal)

    for i in range(len(signal)):
        if i >= window_size:
            window = signal[i-window_size+1:i+1]
            max_val = np.max(window)
            min_val = np.min(window)
            max_min_diff[i] = max_val - min_val
            if max_min_diff[i] >= threshold:
                checked_values[i] = max_val
                if checked_values[i-1] == 0:
                    upto[i] = max_val

    return checked_values, max_min_diff, upto

def calculate_upto_result(upto: np.ndarray):
    peaks = np.where(upto > 0)[0]
    
    if len(peaks) == 0:
        return np.zeros_like(upto)

    intervals = np.diff(peaks)

    if len(intervals) == 0:
        half_avg_interval = 0
    else:
        half_avg_interval = np.mean(intervals) / 2

    result = np.zeros_like(upto)
    
    for i in range(len(peaks)):
        if i == 0:
            result[peaks[i]] = upto[peaks[i]]

        elif (i>0) and (intervals[i-1] >= half_avg_interval):
            result[peaks[i]] = upto[peaks[i]]            

    return result

def calculate_permin(result: np.ndarray, sr: int):
    peaks = np.where(result > 0)[0]
    intervals = np.diff(peaks) / sr
    bpm = 60.0 / np.mean(intervals)
    return bpm

def find_minima_and_calculate_rr(signal: np.ndarray, sampling_rate: int):
    minima, _ = find_peaks(-signal)
    num_inflection_points = len(minima)
    time_duration = len(signal) / sampling_rate
    breaths = num_inflection_points
    respiratory_rate = breaths / time_duration * 60
    
    return respiratory_rate, minima

def normalize_signal(signal: np.ndarray):
    max_val = np.max(signal)
    min_val = np.min(signal)
    if max_val == min_val:
        return np.full_like(signal, 0.5)
    else:
        return (signal - min_val) / (max_val - min_val)


def preprocess_data(time, bcg, sampling_rate=100, normwindow=70, checkwindow=10, checkthereshold=0.75, run_model=False):
    filtered_hr = get_bcg_heartrate_signal(bcg, sampling_rate)
    filtered_rp = get_bcg_respiration_signal(bcg, sampling_rate)
    
    normalized_signal_h = normalize_signal_window(filtered_hr, window_size=normwindow)
    normalized_signal_r = normalize_signal_window(filtered_rp, window_size=normwindow)
    
    checked_values_h, max_min_diff_h, upto_h = calculate_checked_values(normalized_signal_h, window_size=checkwindow, threshold=checkthereshold)
    peak_h = calculate_upto_result(upto_h)
    bpm_h = calculate_permin(peak_h, sampling_rate)
    
    bpm_r, minima_r = find_minima_and_calculate_rr(normalized_signal_r, sampling_rate)
    
    combined_signal = 0.9 * peak_h + 0.1 * normalized_signal_r
    coeffs = pywt.wavedec(combined_signal, 'db4', level=4)
    reconstructed_signal = pywt.waverec(coeffs, 'db4')
    smoothed_reconstructed_signal_gaussian = gaussian_filter1d(reconstructed_signal, sigma=2)
    normalized_reconstructed_signal = normalize_signal(smoothed_reconstructed_signal_gaussian)
    
    peak_h = np.array(peak_h, dtype=np.float64)
    smoothed_peak_h_gaussian = gaussian_filter1d(peak_h, sigma=4)
    normalized_peak_h = normalize_signal(smoothed_peak_h_gaussian)
    
    combined_matrix_for_s = np.column_stack((time, filtered_hr, filtered_rp))
    
    if run_model :
        time_instance = np.stack([normalized_signal_h, normalized_reconstructed_signal, normalized_peak_h], axis=-1)
        
        f,t, Zxx = stft(time_instance.transpose(1,0),fs=100, window='hann',nperseg=125)
        spectrogram_instance = np.abs(Zxx)  #(12, 63, 78)
        spectrogram_instance = spectrogram_instance.transpose(1,2,0)
        
        return bpm_h, bpm_r, combined_matrix_for_s, time_instance, spectrogram_instance
    
    return bpm_h, bpm_r, combined_matrix_for_s, None, None


########## 모델 관련
class MultiHeadedAttention(nn.Module):
    """
    Take in model size and number of heads.
    """
    def __init__(self, h, d_model, dropout=0.1):
        super().__init__()
        assert d_model % h == 0
        # We assume d_v always equals d_k
        self.d_k = d_model // h
        self.h = h
        self.linear_layers = nn.ModuleList([nn.Linear(d_model, d_model) for _ in range(3)])
        self.output_linear = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(p=dropout)
    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)
        # 1) Do all the linear projections in batch from d_model => h x d_k
        query, key, value = [l(x).view(batch_size, -1, self.h, self.d_k).transpose(1, 2)
                             for l, x in zip(self.linear_layers, (query, key, value))]
        # 2) Apply attention on all the projected vectors in batch.
        scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(query.size(-1))
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        attn = F.softmax(scores, dim=-1)
        attn = self.dropout(attn)
        x = torch.matmul(attn, value)
        # 3) "Concat" using a view and apply a final linear.
        x = x.transpose(1, 2).contiguous().view(batch_size, -1, self.h * self.d_k)
        return self.output_linear(x)
class LayerNorm(nn.Module):
    "Construct a layernorm module (See citation for details)."
    def __init__(self, features, eps=1e-6):
        super(LayerNorm, self).__init__()
        self.a_2 = nn.Parameter(torch.ones(features))
        self.b_2 = nn.Parameter(torch.zeros(features))
        self.eps = eps
    def forward(self, x):
        mean = x.mean(-1, keepdim=True)
        std = x.std(-1, keepdim=True)
        return self.a_2 * (x - mean) / (std + self.eps) + self.b_2

class Encoder1D(nn.Module):
    def __init__(self, nc):
        super(Encoder1D, self).__init__()
        ndf = 32
        self.main = nn.Sequential(
            nn.Conv1d(nc, ndf, 4, 2, 1),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv1d(ndf, ndf * 2, 4, 2, 1),
            nn.BatchNorm1d(ndf * 2),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv1d(ndf * 2, ndf * 4, 4, 2, 1),
            nn.BatchNorm1d(ndf * 4),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv1d(ndf * 4, ndf * 8, 4, 2, 1),
            nn.BatchNorm1d(ndf * 8),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv1d(ndf * 8, ndf * 16, 5, 2, 1),
            nn.BatchNorm1d(ndf * 16),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv1d(ndf * 16, 50, 15, 1, 0),
        )

    def forward(self, input):
        output = self.main(input)
        return output

class Decoder1D(nn.Module):
    def __init__(self, nc):
        super(Decoder1D, self).__init__()
        ngf = 32
        self.main=nn.Sequential(
            nn.ConvTranspose1d(50, ngf*16, 15, 1, 0),
            nn.BatchNorm1d(ngf*16),
            nn.ReLU(True),
            nn.ConvTranspose1d(ngf * 16, ngf * 8, 5, 2, 1),
            nn.BatchNorm1d(ngf * 8),
            nn.ReLU(True),
            nn.ConvTranspose1d(ngf * 8, ngf * 4, 4, 2, 1),
            nn.BatchNorm1d(ngf * 4),
            nn.ReLU(True),
            nn.ConvTranspose1d(ngf * 4, ngf*2, 4, 2, 1),
            nn.BatchNorm1d(ngf*2),
            nn.ReLU(True),
            nn.ConvTranspose1d(ngf * 2, ngf, 4, 2, 1),
            nn.BatchNorm1d(ngf),
            nn.ReLU(True),
            nn.ConvTranspose1d(ngf, nc, 4, 2, 1),
            nn.Sigmoid()
        )

    def forward(self, input):
        output = self.main(input)
        return output
    
class Encoder2D(nn.Module):
    def __init__(self, nc):
        super(Encoder2D, self).__init__()
        ndf = 32
        self.main = nn.Sequential(
            nn.Conv2d(nc, ndf, 3, 1, 0),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf, ndf * 2, 3, 1, 1),
            nn.BatchNorm2d(ndf * 2),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf * 2, ndf * 4, 3, 1, 0),
            nn.BatchNorm2d(ndf * 4),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf * 4, ndf * 8, 3, 1, 1),
            nn.BatchNorm2d(ndf * 8),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf * 8, ndf * 16, 3, 1, 0),
            nn.BatchNorm2d(ndf * 16),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf * 16, 50, 3, 1, 0),
        )

    def forward(self, input):
        output = self.main(input)
        return output
    

#Time and Spectrogram Restoration
class TSRNet(nn.Module):

    def __init__(self, enc_in):
        super(TSRNet, self).__init__()

        self.channel = enc_in

        # Time series module 
        self.time_encoder = Encoder1D(enc_in)
        self.time_decoder = Decoder1D(enc_in+1)
        
        # Spectrogram module
        self.spec_encoder = Encoder2D(enc_in)
    
        self.conv_spec1 = nn.Conv1d(50*55, 50, 3, 1, 1, bias=False)
        
        self.mlp = nn.Sequential(
            nn.Linear(5, 3),
            nn.LayerNorm(3),
            nn.ReLU()
        )
        
        self.attn1 = MultiHeadedAttention(2, 50)
        self.drop = nn.Dropout(0.1)
        self.layer_norm1 = LayerNorm(50)

    def attention_func(self,x, attn, norm):
        attn_latent = attn(x, x, x)
        attn_latent = norm(x + self.drop(attn_latent))
        return attn_latent
    
    def forward(self, time_ecg, spectrogram_ecg):
        #Time ECG encode
        time_features = self.time_encoder(time_ecg.transpose(-1,1)) #(32, 50, 136)

        #Spectrogram ECG encode
        spectrogram_features = self.spec_encoder(spectrogram_ecg.permute(0,3,1,2)) #(32, 50, 63, 66)
        n, c, h, w = spectrogram_features.shape
        spectrogram_features = self.conv_spec1(spectrogram_features.contiguous().view(n, c*h, w)) #(32, 50, 66)
        
        latent_combine = torch.cat([time_features, spectrogram_features], dim=-1)
        #Cross-attention
        latent_combine = latent_combine.transpose(-1, 1)
        attn_latent = self.attention_func(latent_combine, self.attn1, self.layer_norm1)
        attn_latent = self.attention_func(attn_latent, self.attn1, self.layer_norm1)
        latent_combine = attn_latent.transpose(-1, 1)
        
        latent_combine = self.mlp(latent_combine)
        
        output = self.time_decoder(latent_combine)
        output = output.transpose(-1, 1)

        return  (output[:,:,0:self.channel],output[:,:,self.channel:self.channel+1])


def TSRNET(model_path, time_instance, spec_instance, threshold):
    model = TSRNet(enc_in=3)
    checkpoint = torch.load(model_path, map_location='cpu', weights_only=True)
    model.load_state_dict(checkpoint['model_state_dict'])
    
    time_bcg = torch.from_numpy(time_instance).float()
    time_bcg = time_bcg.unsqueeze(0)
    
    spec_bcg = torch.from_numpy(spec_instance).float()
    spec_bcg = spec_bcg.unsqueeze(0)
    
    model.eval()
    anomalies_detected = False
    
    with torch.no_grad():
        (gen_time, time_var) = model(time_bcg, spec_bcg)
        time_err = (gen_time - time_bcg) ** 2
        reconstruction_error = torch.mean(time_err).item()

        if reconstruction_error > threshold:
            anomalies_detected = True
            return anomalies_detected, reconstruction_error

    if not anomalies_detected:
        return anomalies_detected, None