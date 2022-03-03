package com.facebook.encapp.utils;

import android.media.MediaCodecInfo;
import android.media.MediaFormat;
import android.util.Size;

import com.facebook.encapp.proto.Configure;
import com.facebook.encapp.proto.DataValueType;
import com.facebook.encapp.proto.Input;
import com.facebook.encapp.proto.Test;


public class TestDefinitionHelper {
    private static String TAG = "encapp";
    public static MediaFormat buildMediaFormat(Test test) {
        Configure config = test.getConfigure();
        Input input = test.getInput();
        Size sourceResolution = SizeUtils.parseXString(input.getResolution());

        MediaFormat format = MediaFormat.createVideoFormat(
                config.getMime().toString(), sourceResolution.getWidth(), sourceResolution.getHeight());

        format.setInteger(MediaFormat.KEY_BIT_RATE, magnitudeToInt(config.getBitrate()));
        format.setFloat(MediaFormat.KEY_FRAME_RATE, input.getFramerate());
        format.setInteger(MediaFormat.KEY_BITRATE_MODE, config.getBitrateMode().getNumber());
        format.setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, config.getIFrameInterval());
       // TODO: format.setInteger(MediaFormat.KEY_COLOR_FORMAT, config.getColorFormat());

        int colorRange = (config.hasColorRange())? config.getColorRange().getNumber():
                                                   MediaFormat.COLOR_RANGE_LIMITED;

        int colorTransfer  = (config.hasColorTransfer())? config.getColorTransfer().getNumber():
                                                          MediaFormat.COLOR_TRANSFER_SDR_VIDEO;
        int colorStandard  = (config.hasColorStandard())? config.getColorStandard().getNumber():
                                                          MediaFormat.COLOR_STANDARD_BT709;

        format.setInteger(MediaFormat.KEY_COLOR_RANGE, colorRange);
        format.setInteger(MediaFormat.KEY_COLOR_STANDARD, colorTransfer);
        format.setInteger(MediaFormat.KEY_COLOR_TRANSFER, colorStandard);

        int bitrateMode = (config.hasBitrateMode())? config.getBitrateMode().getNumber():
                                                    MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_CBR;
        format.setInteger(MediaFormat.KEY_BITRATE_MODE, bitrateMode);
        int qpVal = 30;
        if (bitrateMode == MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_CQ) {
            // Now we need a qp value
            if (config.hasQualityLevel()) {
                qpVal = config.getQualityLevel();
            }
        }

        format.setInteger(MediaFormat.KEY_QUALITY, qpVal);


        for (Configure.Parameter param:config.getParameterList()) {

            switch (param.getType().getNumber()) {
                case DataValueType.floatType_VALUE:
                    float fval = Float.parseFloat(param.getValue());
                    format.setFloat(param.getKey(), fval);
                    break;
                case DataValueType.intType_VALUE:
                    int ival = TestDefinitionHelper.magnitudeToInt(param.getValue());
                    format.setInteger(param.getKey(), ival);
                    break;
                case DataValueType.longType_VALUE:
                    long lval = Long.parseLong(param.getValue());
                    format.setLong(param.getKey(), lval);
                    break;
                case DataValueType.stringType_VALUE:
                    format.setString(param.getKey(), param.getValue());
                    break;
                default:
                    ///Should not be here
            }
        }
        return format;
    }


    public static int magnitudeToInt(String text) {
        int index = text.indexOf("bps");

        if (index > 0) {
            text = text.substring(0, index).trim();
        } else {
            text = text.trim();
        }

        int val = 0;
        if (text.endsWith("k")) {
            val = Integer.parseInt(text.substring(0, text.lastIndexOf('k')).trim()) * 1000;
        } else if (text.endsWith("M")) {
            val = Integer.parseInt(text.substring(0, text.lastIndexOf('M')).trim()) * 1000000;
        } else if (text != null && text.length() > 0){
            val = Integer.parseInt(text);
        } else {
            val = 0;
        }

        return val;
    }

    public static Test updateEncoderResolution(Test test, int width, int height) {
        Test.Builder builder = Test.newBuilder(test);
        builder.setConfigure(Configure.newBuilder(test.getConfigure()).setResolution(width + "x" + height));
        return builder.build();
    }

    public static Test updateInputSettings(Test test, MediaFormat format) {
        Test.Builder builder = test.toBuilder();
        Input.Builder input = builder.getInput().toBuilder();
        input.setResolution(String.valueOf(format.getInteger(MediaFormat.KEY_BIT_RATE)));
        input.setFramerate(format.getFloat(MediaFormat.KEY_FRAME_RATE));

        return builder.build();
    }

    public static Test updatePlayoutFrames(Test test, int frames) {
        Test.Builder builder = Test.newBuilder(test);
        builder.setInput(Input.newBuilder(test.getInput()).setPlayoutFrames(frames));
        return builder.build();
    }



    public static Test checkAnUpdateBasicSettings(Test test) {
        // Make sure we have the most basic settings well defined
        Size res;
        Input.Builder input = test.getInput().toBuilder();
        if (!input.hasResolution()) {
            input.setResolution("1280x720");
        }

        if (!input.hasFramerate()) {
            input.setFramerate(30.0f);
        }

        Configure.Builder config = test.getConfigure().toBuilder();
        if (!config.hasBitrate()) {
            config.setBitrate("1 Mbps");
        }

        if (!config.hasFramerate()) {
            config.setFramerate(input.getFramerate());
        }

        if (!config.hasIFrameInterval()) {
            config.setIFrameInterval(10);
        }
        if (!config.hasResolution()) {
            config.setResolution(input.getResolution());
        }

        Test.Builder builder = test.toBuilder();
        builder.setInput(input);
        builder.setConfigure(config);

        return builder.build();
    }
}
