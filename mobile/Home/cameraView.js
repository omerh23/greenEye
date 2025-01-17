import React, {useRef, useEffect, useState} from 'react';
import {View, TouchableOpacity, Text, StyleSheet, Image, Dimensions} from 'react-native';
import { Camera, useCameraDevice, useCameraPermission, useCameraFormat } from 'react-native-vision-camera';
import EntypoIcon from 'react-native-vector-icons/Entypo';
import { useNavigation } from '@react-navigation/native';
import RNFS from "react-native-fs";
import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";
import axiosInstance from '../axiosConfig';

const CameraView = () => {
    const camera = useRef(null);
    const { hasPermission, requestPermission } = useCameraPermission();
    const device = useCameraDevice('back');
    const format = useCameraFormat(device, [
        { photoResolution: { width: 1280, height: 720 } },
      ])
    const navigation = useNavigation();
    const [imageSource, setImageSource] = useState('');
    const [token, setToken] = useState(null);
    const [imageDetails, setImageDetails] = useState("");
    const [isImageFromCls,setIsImageFromCls] = useState(false);

    useEffect(() => {
        const initializeCamera = async () => {
            try {
                await requestPermission();
                
                const storedToken = await AsyncStorage.getItem('token');
                setToken(storedToken);
            } catch (error) {
                console.error('Error initializing camera:', error);
            }
        };
        initializeCamera();
    }, []);

    const handleClose = () => {
        navigation.goBack();
    };

    

    async function HandlePhoto() {
        try {
            setImageDetails('');
            setIsImageFromCls(false);
            
            const photo = await camera.current.takePhoto();

            setImageSource(`file://${photo.path}`);
            setImageDetails("waiting for results..");
            const base64Image = await RNFS.readFile(photo.path, 'base64');
            const broadcastCamera = false;
            const response = await axiosInstance.post('/selfCamera', { base64Image, token,broadcastCamera });
            console.log('Image uploaded successfully');
            const { label, confidence, image } = response.data;
            const detailString = `Result: ${label} Confidence: ${confidence}%`;
            setImageDetails(detailString);

            if (image) {
                setImageSource(`data:image/jpeg;base64,${image}`);
                setIsImageFromCls(true);

            }

            console.log(detailString);
        } catch (e) {
            console.error('Error fetching data:', e);
        }
    }

    function closeCapture() {
        setImageSource('');
        setIsImageFromCls(false);
    }

    return (
        <View style={styles.container}>
            <View style={styles.cameraContainer}>
                <Camera
                    ref={camera}
                    style={styles.cameraStyle}
                    device={device}
                    isActive={true}
                    photo={true}
                    format={format}
                />
                <TouchableOpacity style={styles.closeButton} onPress={handleClose}>
                    <EntypoIcon name="arrow-long-right" size={40} color="#2a7312" />
                    <Text style={styles.buttonText2}>Home</Text>
                </TouchableOpacity>
            </View>

            <TouchableOpacity style={styles.captureButton} onPress={HandlePhoto}>
                <EntypoIcon name="camera" size={40} color="#2a7312" />
                <Text style={styles.buttonText2}>Take Photo</Text>
                <Text style={styles.result}>{imageDetails}</Text>

            </TouchableOpacity>
            {imageSource ? (
                <View style={styles.previewContainer}>
                    <Text style={styles.buttonText2}>Preview</Text>
                    <Image
                        source={{ uri: imageSource }}
                        style={styles.previewImage}
                        resizeMode="cover"
                    />

                    <TouchableOpacity style={styles.CloseCaptureButton} onPress={closeCapture}>
                        <EntypoIcon name="cross" size={40} color="#2a7312" />
                    </TouchableOpacity>
                </View>
            ) : null}
        </View>
    );
};

const SCREEN_WIDTH = Dimensions.get("screen").width;

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: 'white',

    },
    cameraContainer: {
        width: SCREEN_WIDTH,
        height: 300,
    },
    cameraStyle: {
        flex: 1,
    },
    closeButton: {
        position: 'absolute',
        top: 16,
        right: 5,
    },
    previewContainer: {
        justifyContent: "center",
        alignItems: "center",
        marginTop:25,
    },
    previewImage: {
        width: 300,
        height: 200,
        borderRadius: 10,
    },
    
    buttonText2: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#2a7312',
    },
    captureButton: {
        alignItems: 'center',
        position: 'relative',
        color: 'green',
        marginTop:15,
        
    },
    CloseCaptureButton: {
        alignItems: 'center',
        position: 'absolute',
        top: 20,
    },
    result: {
        marginTop: 20,
        fontSize: 20,
        color: "green",
    }
});

export default CameraView;
