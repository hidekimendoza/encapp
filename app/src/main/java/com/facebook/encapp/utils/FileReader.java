package com.facebook.encapp.utils;

import android.util.Log;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.ByteBuffer;

public class FileReader {
    private static final String TAG = "encapp";
    File mFile;
    BufferedInputStream mBis;
    public FileReader() {
    }

    public boolean openFile(String name) {
        try {
            Log.e(TAG, "Open file");
            mFile = new File(name);
            mBis = new BufferedInputStream(new FileInputStream(mFile));
        } catch (FileNotFoundException e) {
            Log.e(TAG, "Failed to open file: "+name + ", "+ e.getMessage());
            e.printStackTrace();
            return false;
        }
        return true;
    }

    public void closeFile() {
        try {
            synchronized (this) {
                Log.e(TAG, "Close file");
                if (mBis != null) {
                    mBis.close();
                    mBis = null;
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public int fillBuffer(ByteBuffer buffer, int size){
        synchronized (this) {
            if (mBis == null) return 0;
        }
        if (buffer.hasArray()) {
            byte[] bytes = buffer.array();
            try {
                int read = mBis.read(bytes, 0, bytes.length);
                return read;
            } catch (IOException e) {
                e.printStackTrace();
                return 0;
            }
        } else {
            byte[] bytes = new byte[size];
            try {
                int read = mBis.read(bytes, 0, bytes.length);
                buffer.put(bytes);
                return read;
            } catch (IOException e) {
                Log.e(TAG, "error: " + e.getMessage());
                e.printStackTrace();
                return 0;
            }
        }
    }
}
