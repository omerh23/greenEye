// Sidebar.js
import {View, Text, TouchableOpacity, StyleSheet, Image} from 'react-native';
import React, {useState} from "react";
import { Icon } from 'react-native-elements'
import EntypoIcon from 'react-native-vector-icons/Entypo';

const Sidebar = () => {
    const [buttonPressed, setButtonPressed] = useState(false);

    function toggleSidebar() {
        setButtonPressed(!buttonPressed);
    }

    return (
        <View style={styles.container}>

            <View style={styles.mainbutton}>
                <TouchableOpacity  onPress={toggleSidebar}>
                    <EntypoIcon name="list" size={35} color="black" />

                </TouchableOpacity>
            </View>


            {buttonPressed && (
                <View style={styles.containButtons}>

                    <TouchableOpacity style={styles.sidebarbuttons} >
                        <EntypoIcon name="login" size={35} color="black" />
                        <Text>Logout</Text>
                    </TouchableOpacity>

                    <TouchableOpacity style={styles.sidebarbuttons} >
                        <EntypoIcon name="book" size={35} color="black" />
                        <Text>Guide</Text>
                    </TouchableOpacity>

                    <TouchableOpacity style={styles.sidebarbuttons} >
                        <EntypoIcon name="cog" size={35} color="black" />
                        <Text>Setting</Text>
                    </TouchableOpacity>

                    <TouchableOpacity style={styles.sidebarbuttons} >
                        <EntypoIcon name="layers" size={35} color="black" />
                        <Text>T&P</Text>
                    </TouchableOpacity>

                    <TouchableOpacity style={styles.sidebarbuttons} >
                        <EntypoIcon name="megaphone" size={35} color="black" />
                        <Text>Feedback</Text>
                    </TouchableOpacity>

                    <TouchableOpacity style={styles.sidebarbuttons} >
                        <EntypoIcon name="slideshare" size={35} color="black" />
                        <Text>About us</Text>
                    </TouchableOpacity>

                </View>

            )}


        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    closeButton: {
        bottom: 0,
    },

    containButtons: {
        padding: 15,
        position: 'absolute',
        right: -5,
        top: 60,
        width: 100,
        backgroundColor: 'rgba(255, 255, 255, 0.7)',
        borderRadius: 10,
        alignItems: 'center',
    },
    mainbutton: {
        position: 'absolute',
        top: 15, // Adjust the top position as needed
        right: 0, // Adjust the right position as needed
        fontSize: 25,
        fontWeight: 'bold',
        color: '#000',
    },
    sidebarbuttons: {
        marginBottom: 20,
        alignItems: 'center',

    }
});

export default Sidebar;
