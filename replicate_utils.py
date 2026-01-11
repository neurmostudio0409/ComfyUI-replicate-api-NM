"""
Utility functions for handling video and audio in ComfyUI
"""

import os
import cv2
import tempfile
import numpy as np
import torch

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    print("⚠️ soundfile not available. Audio processing may be limited.")


class VideoUtils:
    """Utilities for handling video data"""
    
    @staticmethod
    def save_video_from_path(video_path):
        """
        If video is already a path, just return it
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            str: Path to video file
        """
        if isinstance(video_path, str) and os.path.exists(video_path):
            return video_path
        return None
    
    @staticmethod
    def save_image_sequence_to_video(images, output_path=None, fps=24):
        """
        Convert ComfyUI image tensor to video file
        
        Args:
            images: Tensor of images [B, H, W, C] in range [0, 1]
            output_path (str, optional): Output path. If None, creates temp file
            fps (int): Frames per second
            
        Returns:
            str: Path to saved video file
        """
        try:
            # Convert tensor to numpy if needed
            if isinstance(images, torch.Tensor):
                images = images.cpu().numpy()
            
            # Ensure correct shape [B, H, W, C]
            if len(images.shape) != 4:
                print(f"❌ Expected 4D tensor, got shape: {images.shape}")
                return None
            
            batch_size, height, width, channels = images.shape
            
            # Convert to uint8 [0, 255]
            if images.dtype == np.float32 or images.dtype == np.float64:
                images = (images * 255).astype(np.uint8)
            
            # Create output path if not provided
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                output_path = temp_file.name
                temp_file.close()
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                print(f"❌ Failed to create video writer")
                return None
            
            # Write frames
            for i in range(batch_size):
                frame = images[i]
                # Convert RGB to BGR for OpenCV
                if channels == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                out.write(frame)
            
            out.release()
            
            print(f"✅ Video saved: {output_path}")
            print(f"   Frames: {batch_size}, Size: {width}x{height}, FPS: {fps}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Failed to save video: {e}")
            return None
    
    @staticmethod
    def get_video_path(video_input):
        """
        Extract video file path from various input formats
        
        Args:
            video_input: Could be a path string, VideoWrapper object, or other format
            
        Returns:
            str: Path to video file, or None
        """
        # If it's a string path
        if isinstance(video_input, str):
            if os.path.exists(video_input):
                return video_input
        
        # If it has a get_path method (like VideoWrapper)
        if hasattr(video_input, 'get_path'):
            return video_input.get_path()
        
        # If it has a video_path attribute
        if hasattr(video_input, 'video_path'):
            return video_input.video_path
        
        # If it's a dict with path
        if isinstance(video_input, dict) and 'path' in video_input:
            return video_input['path']
        
        return None


class AudioUtils:
    """Utilities for handling audio data"""
    
    @staticmethod
    def save_audio_from_comfyui(audio_input, output_path=None):
        """
        Convert ComfyUI audio format to WAV file
        
        Args:
            audio_input: ComfyUI audio format (dict with waveform and sample_rate)
            output_path (str, optional): Output path. If None, creates temp file
            
        Returns:
            str: Path to saved audio file, or None if failed
        """
        if audio_input is None:
            print("⚠️ Audio input is None")
            return None
        
        try:
            # Debug: print audio input structure
            print(f"🔍 Audio input type: {type(audio_input)}")
            if isinstance(audio_input, dict):
                print(f"🔍 Audio dict keys: {audio_input.keys()}")
            elif hasattr(audio_input, '__dict__'):
                print(f"🔍 Audio attributes: {list(audio_input.__dict__.keys())}")
            
            # Handle different possible audio formats
            waveform = None
            sample_rate = 44100
            
            if isinstance(audio_input, dict):
                waveform = audio_input.get('waveform')
                sample_rate = audio_input.get('sample_rate', 44100)
            elif hasattr(audio_input, 'waveform'):
                waveform = audio_input.waveform
                sample_rate = getattr(audio_input, 'sample_rate', 44100)
            else:
                print(f"⚠️ Unsupported audio format: {type(audio_input)}")
                return None
            
            if waveform is None:
                print("⚠️ No waveform data found in audio input")
                return None
            
            # Debug: print waveform info
            print(f"🔍 Waveform type: {type(waveform)}")
            if hasattr(waveform, 'shape'):
                print(f"🔍 Waveform shape: {waveform.shape}")
            if hasattr(waveform, 'dtype'):
                print(f"🔍 Waveform dtype: {waveform.dtype}")
            
            # Convert tensor to numpy if needed
            if isinstance(waveform, torch.Tensor):
                waveform = waveform.cpu().numpy()
                print(f"🔍 Converted to numpy, shape: {waveform.shape}")
            elif hasattr(waveform, 'numpy'):
                waveform = waveform.numpy()
                print(f"🔍 Converted to numpy, shape: {waveform.shape}")
            
            # Ensure proper shape
            original_shape = waveform.shape
            if len(waveform.shape) > 1:
                # If stereo, convert to mono by averaging channels
                if waveform.shape[0] == 2:  # Channels first [2, N]
                    print(f"🔍 Converting stereo (channels first) to mono")
                    waveform = np.mean(waveform, axis=0)
                elif waveform.shape[1] == 2:  # Channels last [N, 2]
                    print(f"🔍 Converting stereo (channels last) to mono")
                    waveform = np.mean(waveform, axis=1)
                elif len(waveform.shape) == 3:  # [1, C, N] or similar
                    print(f"🔍 Squeezing 3D shape")
                    waveform = waveform.squeeze()
                    if len(waveform.shape) > 1:
                        waveform = np.mean(waveform, axis=0)
                else:
                    print(f"🔍 Squeezing shape")
                    waveform = waveform.squeeze()
            
            print(f"🔍 After shape processing: {waveform.shape}")
            
            # Ensure 1D array
            if len(waveform.shape) > 1:
                waveform = waveform.flatten()
                print(f"🔍 Flattened to: {waveform.shape}")
            
            # Normalize audio to [-1, 1] range
            if waveform.dtype != np.float32 and waveform.dtype != np.float64:
                if waveform.dtype == np.int16:
                    print(f"🔍 Converting int16 to float32")
                    waveform = waveform.astype(np.float32) / 32768.0
                elif waveform.dtype == np.int32:
                    print(f"🔍 Converting int32 to float32")
                    waveform = waveform.astype(np.float32) / 2147483648.0
                else:
                    print(f"🔍 Converting {waveform.dtype} to float32")
                    waveform = waveform.astype(np.float32)
            else:
                waveform = waveform.astype(np.float32)
            
            # Clip to valid range
            waveform = np.clip(waveform, -1.0, 1.0)
            
            # Create output path if not provided
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                output_path = temp_file.name
                temp_file.close()
            
            print(f"🔍 Final waveform shape: {waveform.shape}, dtype: {waveform.dtype}, sample_rate: {sample_rate}")
            
            # Try different methods to save audio
            if SOUNDFILE_AVAILABLE:
                try:
                    sf.write(output_path, waveform, int(sample_rate))
                    print(f"✅ Audio saved with soundfile: {output_path}")
                except Exception as e:
                    print(f"⚠️ soundfile failed: {e}")
                    # Try scipy as backup
                    try:
                        from scipy.io import wavfile
                        # Convert to int16 for scipy
                        waveform_int16 = (waveform * 32767).astype(np.int16)
                        wavfile.write(output_path, int(sample_rate), waveform_int16)
                        print(f"✅ Audio saved with scipy: {output_path}")
                    except Exception as e2:
                        print(f"❌ scipy also failed: {e2}")
                        return None
            else:
                # Try scipy as primary method
                try:
                    from scipy.io import wavfile
                    waveform_int16 = (waveform * 32767).astype(np.int16)
                    wavfile.write(output_path, int(sample_rate), waveform_int16)
                    print(f"✅ Audio saved with scipy: {output_path}")
                except Exception as e:
                    print(f"❌ scipy failed: {e}")
                    return None
            
            print(f"   Duration: {len(waveform)/sample_rate:.2f}s @ {sample_rate}Hz")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Failed to save audio: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_audio_path(audio_input):
        """
        Extract audio file path from various input formats
        
        Args:
            audio_input: Could be a path string or ComfyUI audio format
            
        Returns:
            str: Path to audio file, or None
        """
        # If it's a string path
        if isinstance(audio_input, str):
            if os.path.exists(audio_input):
                return audio_input
        
        # If it has a path attribute
        if hasattr(audio_input, 'path'):
            return audio_input.path
        
        # If it's a dict with path
        if isinstance(audio_input, dict) and 'path' in audio_input:
            return audio_input['path']
        
        # Otherwise, need to save it
        return AudioUtils.save_audio_from_comfyui(audio_input)


class ImageUtils:
    """Utilities for handling image data"""
    
    @staticmethod
    def save_image_tensor(image_tensor, output_path=None):
        """
        Save image tensor to file
        
        Args:
            image_tensor: Tensor of images [B, H, W, C] or [H, W, C] in range [0, 1]
            output_path (str, optional): Output path. If None, creates temp file
            
        Returns:
            str: Path to saved image file
        """
        try:
            # Convert tensor to numpy if needed
            if isinstance(image_tensor, torch.Tensor):
                image_tensor = image_tensor.cpu().numpy()
            
            # Handle batch dimension
            if len(image_tensor.shape) == 4:
                # Take first image from batch [B, H, W, C] -> [H, W, C]
                image = image_tensor[0]
            elif len(image_tensor.shape) == 3:
                image = image_tensor
            else:
                print(f"❌ Unexpected image shape: {image_tensor.shape}")
                return None
            
            # Convert to uint8 [0, 255]
            if image.dtype == np.float32 or image.dtype == np.float64:
                image = (image * 255).astype(np.uint8)
            
            # Create output path if not provided
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                output_path = temp_file.name
                temp_file.close()
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            # Convert RGB to BGR for OpenCV
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            else:
                image_bgr = image
            
            # Save image
            cv2.imwrite(output_path, image_bgr)
            
            print(f"✅ Image saved: {output_path}")
            print(f"   Size: {image.shape[1]}x{image.shape[0]}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Failed to save image: {e}")
            import traceback
            traceback.print_exc()
            return None


def cleanup_temp_file(file_path):
    """Clean up temporary file"""
    if file_path and os.path.exists(file_path) and '/tmp/' in file_path or '\\Temp\\' in file_path:
        try:
            os.remove(file_path)
            print(f"🗑️ Cleaned up temp file: {file_path}")
        except Exception as e:
            print(f"⚠️ Could not clean up temp file: {e}")
