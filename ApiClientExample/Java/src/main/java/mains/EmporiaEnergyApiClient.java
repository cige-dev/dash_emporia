package mains;


import static java.util.stream.Collectors.toList;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.concurrent.TimeUnit;

import com.emporiaenergy.partnerapi2.AuthenticationRequest;
import com.emporiaenergy.partnerapi2.AuthenticationResponse;
import com.emporiaenergy.partnerapi2.BatteriesResponse;
import com.emporiaenergy.partnerapi2.Battery;
import com.emporiaenergy.partnerapi2.BatterySettings;
import com.emporiaenergy.partnerapi2.BatterySettings.ChargeToStateOfCharge;
import com.emporiaenergy.partnerapi2.BatterySettings.ChargeWithExcessSolar;
import com.emporiaenergy.partnerapi2.BatterySettings.DischargeToStateOfCharge;
import com.emporiaenergy.partnerapi2.BatterySettings.Idle;
import com.emporiaenergy.partnerapi2.BatterySettings.LoadFollowing;
import com.emporiaenergy.partnerapi2.DataResolution;
import com.emporiaenergy.partnerapi2.DeviceInventoryRequest;
import com.emporiaenergy.partnerapi2.DeviceInventoryResponse;
import com.emporiaenergy.partnerapi2.DeviceInventoryResponse.Device;
import com.emporiaenergy.partnerapi2.DeviceInventoryResponse.Device.CircuitInfo;
import com.emporiaenergy.partnerapi2.DeviceInventoryResponse.Device.DeviceModel;
import com.emporiaenergy.partnerapi2.DeviceUsageRequest;
import com.emporiaenergy.partnerapi2.DeviceUsageRequest.UsageChannel;
import com.emporiaenergy.partnerapi2.DeviceUsageResponse;
import com.emporiaenergy.partnerapi2.DeviceUsageResponse.DeviceUsage;
import com.emporiaenergy.partnerapi2.EVCharger;
import com.emporiaenergy.partnerapi2.EVChargerSettings;
import com.emporiaenergy.partnerapi2.EVChargersResponse;
import com.emporiaenergy.partnerapi2.ListDevicesRequest;
import com.emporiaenergy.partnerapi2.OutletSettings;
import com.emporiaenergy.partnerapi2.OutletsResponse;
import com.emporiaenergy.partnerapi2.PartnerApiGrpc;
import com.emporiaenergy.partnerapi2.PartnerApiGrpc.PartnerApiBlockingStub;
import com.emporiaenergy.partnerapi2.UpdateBatteriesRequest;
import com.emporiaenergy.partnerapi2.UpdateEVChargersRequest;
import com.emporiaenergy.partnerapi2.UpdateOutletsRequest;
import com.google.protobuf.BoolValue;
import com.google.protobuf.DoubleValue;
import com.google.protobuf.UInt32Value;

import io.grpc.Channel;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.StatusRuntimeException;

/**
 * A sample client for the Emporia Energy Partner API.  This works with the PartnerApi2 service that
 * is defined in the partner_api2.proto file.  
 * 
 * If you are migrating from V1 of the API, it is important to remove .usePlaintext() when creating your
 * channel since the new API requires the use of SSL.
 */
public class EmporiaEnergyApiClient
{
	static final String host = "partner.emporiaenergy.com";			// the Emporia Energy partner API
	static final int port = 50052;									// this is the V2 of the Partner API, the V1 was previously available on port 50051
	
	/**
	 * Demonstration program that connects to Emporia Energy's Partner API and return device information. 
	 * {@code arg0} is the partner email address 
	 * {@code arg1} is the partner's password for logging into the Partner Portal at partner.emporiaenergy.com
	 */
	public static void main( String[] args ) throws Exception
	{
		if( args.length != 2 )
		{
			System.err.println( "Usage: partner_email partner_password" );
			System.err.println( "" );
			System.err.println( "  partnerEmail	- the email you use to login to the portal at http://partner.emporiaenergy.com" );
			System.exit( 1 );
		}
		String partnerEmail = args[0];
		String partnerPassword = args[1];

		// Create a communication channel to the server, known as a Channel. Channels are thread-safe
		// and reusable. It is common to create channels at the beginning of your application and reuse
		// them until the application shuts down.
		ManagedChannel channel = ManagedChannelBuilder.forTarget( host + ":" + port ).build();

		logOutput( "EmporiaEnergyApiClient connected to the gRPC API at %s:%d", host, port );

		// make a series of API calls to the Partner API
		EmporiaEnergyApiClient.apiCalls( channel, partnerEmail, partnerPassword );
	}
	
	/**
	 * Exercise the Emporia Energy Partner API which is a gRPC API
	 */
	static public void apiCalls( final Channel channel, final String partnerEmail, final String partnerPw ) throws Exception
	{
		// this code is written against the partner_api2.proto which is V2 of the Partner API
		PartnerApiGrpc.PartnerApiBlockingStub blockingStubV2 = PartnerApiGrpc.newBlockingStub( channel );

		try
		{
			// authenticate with partner email and PW
			AuthenticationRequest request = AuthenticationRequest.newBuilder().setPartnerEmail( partnerEmail ).setPassword( partnerPw ).build();
			AuthenticationResponse authResponse = blockingStubV2.authenticate( request );
			final String authToken = authResponse.getAuthToken();

			// get list of devices managed by partner
			DeviceInventoryRequest inventoryRequest = DeviceInventoryRequest.newBuilder().setAuthToken( authToken ).build();
			DeviceInventoryResponse inventoryResponse = blockingStubV2.getDevices( inventoryRequest );

			// display device information
			logOutput( "Your partner account has %d devices associated to it.", inventoryResponse.getDevicesCount() ); 
			logOutput("*******\n");
			
			List<Device> vue2s = inventoryResponse.getDevicesList().stream().filter( d -> d.getModel().equals(DeviceModel.Vue2) ).collect( toList() );
			logOutput( "Your partner account has %d Vue2s associated to it.", vue2s.size() ); 
			if( !vue2s.isEmpty() )
			{
				logOutput( "Here are the details of the first Vue2 :" ); 
				Device firstVue2 = vue2s.get(0);
				logOutput( "Manufacturer Device Id %24s", firstVue2.getManufacturerDeviceId());
				logOutput( "                 Model %24s", firstVue2.getModel());
				logOutput( "                  Name %24s", firstVue2.getDeviceName());
				logOutput( "      Device Connected %24s", firstVue2.getDeviceConnected());
	
				logOutput( "Here are the circuit_infos describing the circuits available on this device:" );
				for(CircuitInfo circuitInfo : firstVue2.getCircuitInfosList())
					logOutput( "%2s %20s %20s %20s %20s", circuitInfo.getChannelNumber(), circuitInfo.getType(), circuitInfo.getEnergyDirection(), circuitInfo.getSubType(), circuitInfo.getName());
				logOutput("*******\n");
				
				// request energy usage data for all the Vue2s; we are requesting 15min bars covering a recent hour
				// due to the buffering of device data, we don't request data for the most recent 30 minutes
				List<String> vueManufacturerDeviceIds = vue2s.stream().map( device -> device.getManufacturerDeviceId() ).collect( toList() );
			
				long thirtyMinutesAgo = Instant.now().minus(30, ChronoUnit.MINUTES).getEpochSecond();
				// this request will request usage for all the Vue2s in a single call to the API
				DeviceUsageRequest usageRequest = DeviceUsageRequest.newBuilder()
						.setAuthToken( authToken )
						.setStartEpochSeconds( thirtyMinutesAgo - TimeUnit.HOURS.toSeconds( 1 ) )
						.setEndEpochSeconds( thirtyMinutesAgo )
						.setScale( DataResolution.FifteenMinutes )
						.setChannels( UsageChannel.MAINS )		// the MAINS requests only the Mains circuits, not the expansions
						.addAllManufacturerDeviceIds( vueManufacturerDeviceIds )
						.build();
				DeviceUsageResponse usageResponse = blockingStubV2.getUsageData( usageRequest );
				for(DeviceUsage usage : usageResponse.getDeviceUsagesList()) 
				{
					Device vue2 = vue2s.stream().filter(d -> d.getManufacturerDeviceId().equals(usage.getManufacturerDeviceId())).findAny().get();
					logOutput( "Vue2 named '%s' (%s) Energy (kWhs) & Power (kWatts) on the 3 mains channels over recent 15 minute buckets:", vue2.getDeviceName(), vue2.getManufacturerDeviceId() );
					for( int i = 0; i < usage.getBucketEpochSecondsCount(); ++i )
					{
						logOutput( "%s: kWhs / kWatts", Instant.ofEpochSecond( usage.getBucketEpochSeconds( i ) ) );
						for( int channelIndex = 0; channelIndex < usage.getChannelUsagesCount(); ++channelIndex )
						{
							double kWhs = usage.getChannelUsages( channelIndex ).getUsages( i ) / 1000d;		// convert from watt-hours to kWhs
							// multiply by 4 to get to power since this is 15min energy; using 2 kWhs of energy in 15 minutes is consuming at a 8 kWatts rate
							double kWatts = kWhs * 4;		
							logOutput( "  (%d) %.2f / %.2f", usage.getChannelUsages( channelIndex ).getChannel(), kWhs, kWatts );
						}
						logOutput("");
					}
				}
				logOutput("*******\n");
			}
			logOutput("*******\n");

			// find any outlet devices
			List<Device> outlets = inventoryResponse.getDevicesList().stream().filter( d -> d.getModel().equals(DeviceModel.Outlet) ).collect( toList() );
			List<Device> connectedOutlets = outlets.stream().filter( o -> o.getDeviceConnected() ).collect( toList() );
			logOutput( "Your partner account has %d outlets; %s are connected to the Emporia cloud.", outlets.size(), connectedOutlets.size() ); 
			if( !connectedOutlets.isEmpty() )
			{
				Device outlet = connectedOutlets.get( 0 );
				ListDevicesRequest outletRequest = ListDevicesRequest.newBuilder()
						.setAuthToken( authToken )
						.addManufacturerDeviceIds( outlet.getManufacturerDeviceId() )
						.build();
				OutletsResponse outletResponse = blockingStubV2.listOutlets( outletRequest );
				
				OutletSettings status = outletResponse.getOutlets( 0 );
				logOutput( "Here are the details of the first connected SmartPlug:" ); 
				logOutput( "Manufacturer Device Id %24s", outlet.getManufacturerDeviceId());
				logOutput( "                 Model %24s", outlet.getModel());
				logOutput( "                  Name %24s", outlet.getDeviceName());
				logOutput( "      Device Connected %24s", outlet.getDeviceConnected());
				logOutput( "             Outlet On %24s", status.getOn());

				// while we could request the usage data, instead we are going to turn the Outlet On or Off
				UpdateOutletsRequest updateRequest = UpdateOutletsRequest.newBuilder()
						.setAuthToken( authToken )
						.addOutlets( status.toBuilder().setOn( !status.getOn() ).build() )
						.build();
				
				OutletsResponse updateResponse = blockingStubV2.updateOutlets( updateRequest );
				if( updateResponse.getOutletsCount() > 0 )		// will return us the device if it was changed to the new setting
				{
					logOutput( "Changed %s to %s", status.getManufacturerDeviceId(), updateResponse.getOutlets( 0 ).getOn() ? "ON" : "OFF" ); 
	
					logOutput( "Sleeping for one second..." ); 
					Thread.sleep( 1000 );
					
					updateRequest = UpdateOutletsRequest.newBuilder()
							.setAuthToken( authToken )
							.addOutlets( status )
							.build();
					updateResponse = blockingStubV2.updateOutlets( updateRequest );
					logOutput( "Turned %s back %s", status.getManufacturerDeviceId(), updateResponse.getOutlets( 0 ).getOn() ? "ON" : "OFF" );
				}
			}
			logOutput("*******\n");
			
			// find any chargers 
			List<Device> chargers = inventoryResponse.getDevicesList().stream().filter( d -> d.getModel().equals(DeviceModel.EVCharger) ).collect( toList() );
			logOutput( "Your partner account has %d EV Chargers associated to it.", chargers.size() );
			if( !chargers.isEmpty() )
			{
				Device charger = chargers.get( 0 );
				ListDevicesRequest chargerRequest = ListDevicesRequest.newBuilder()
						.setAuthToken( authToken )
						.addManufacturerDeviceIds( charger.getManufacturerDeviceId() )
						.build();
				EVChargersResponse listEVChargersResponse = blockingStubV2.listEVChargers( chargerRequest );
				
				EVCharger status = listEVChargersResponse.getEvchargers( 0 );
				logOutput( "Here are the details of the first one:" ); 
				logOutput( "Manufacturer Device Id %24s", charger.getManufacturerDeviceId());
				logOutput( "                 Model %24s", charger.getModel());
				logOutput( "                  Name %24s", charger.getDeviceName());
				logOutput( "      Device Connected %24s", charger.getDeviceConnected());
				logOutput( "         Car Connected %24s", status.getCarConnected());
				logOutput( "          Car Charging %24s", status.getCarCharging());
				logOutput( "  Max Charge Rate Amps %24s", status.getMaxChargeRateAmps());
				logOutput( "            Charger On %24s", status.getSettings().getOn().getValue());
				logOutput( "      Charge Rate Amps %24s", status.getSettings().getChargeRateAmps().getValue());
				
				// now we change the charger to a different setting and then put it back 
				EVChargerSettings originalSettings = status.getSettings();
				
				logOutput( "Changing charger to off at a rate of 10 amps" );
				changeEVChargerToSettings( blockingStubV2, authToken, charger, 
						originalSettings.toBuilder()
							.setOn( BoolValue.of(false) )
							.setChargeRateAmps( UInt32Value.of(10) )
							.build() );
				Thread.sleep( 1000 );
				
				logOutput( "cause an error by trying to set the charger rate impossibly high" );
				try
				{
					changeEVChargerToSettings( blockingStubV2, authToken, charger, originalSettings.toBuilder()
							.setChargeRateAmps( UInt32Value.of(100) )
							.build() );
				}
				catch(StatusRuntimeException invalidArgument)
				{
					logOutput( "Caught the expected exception: " + invalidArgument.getMessage() );
				}
				
				// now change it back to the original settings
				logOutput( "\n*** Setting the EVCharger back to the original settings" );
				changeEVChargerToSettings( blockingStubV2, authToken, charger, originalSettings );
			}
			logOutput("*******\n");
			
			// find any batteries 
			List<Device> batteries = inventoryResponse.getDevicesList().stream().filter( d -> d.getModel().equals(DeviceModel.Battery) ).collect( toList() );
			logOutput( "Your partner account has %d Batteries associated to it.", batteries.size() );
			if( !batteries.isEmpty() )
			{
				Device battery = batteries.get( 0 );
				ListDevicesRequest batteryRequest = ListDevicesRequest.newBuilder()
						.setAuthToken( authToken )
						.addManufacturerDeviceIds( battery.getManufacturerDeviceId() )
						.build();
				BatteriesResponse listBatteriesResponse = blockingStubV2.listBatteries( batteryRequest );
				
				Battery status = listBatteriesResponse.getBatteries( 0 );
				logOutput( "Here are the details of the first one:" ); 
				logOutput( "Manufacturer Device Id %24s", battery.getManufacturerDeviceId());
				logOutput( "                 Model %24s", battery.getModel());
				logOutput( "                  Name %24s", battery.getDeviceName());
				logOutput( "      Device Connected %24s", battery.getDeviceConnected());
				logOutput( "          Capacity kWh %24s", status.getCapacityKwhs());
				logOutput( " Inverter Max Power kW %24s", status.getInverterMaxPowerKwatts());
				String socPercentage = String.format("%24.1f", status.hasSocPercentage() ? status.getSocPercentage().getValue() : 0.0f);
				logOutput( "           Current SOC %s", (status.hasSocPercentage() ? socPercentage : "Server did not set SoC"));
				logOutput( "           Reserve SOC %24.1f", status.getSettings().getReserveSocPercentage().getValue());
				logOutput( "         Dispatch Mode %24s", status.getSettings().getDispatchModeCase().name());
				
				// now we change the battery to several different settings and then put it back 
				BatterySettings originalSettings = status.getSettings();
				
				logOutput( "Changing battery to a lower Reserve State of Charge" );
				changeBatteryToSettings( blockingStubV2, authToken, battery, originalSettings.toBuilder()
						.setReserveSocPercentage( 
								DoubleValue.of( originalSettings.getReserveSocPercentage().getValue() - 1d )
								).build() );
				Thread.sleep( 1000 );
				
				logOutput( "Set battery to Load Following at 2 kWatts" );
				changeBatteryToSettings( blockingStubV2, authToken, battery, originalSettings.toBuilder()
						.setLoadFollowing( LoadFollowing.newBuilder()
								.setPowerKwatts( DoubleValue.of( 2d ) )
								).build() );
				Thread.sleep( 1000 );

				logOutput( "Set battery to charge from Excess Solar" );
				changeBatteryToSettings( blockingStubV2, authToken, battery, originalSettings.toBuilder()
						.setChargeWithExcessSolar( ChargeWithExcessSolar.newBuilder()
								.setChargePowerKwatts( DoubleValue.of( 5d ) )
								).build() );
				Thread.sleep( 1000 );

				logOutput( "Set battery to charge to 90 percent" );
				changeBatteryToSettings( blockingStubV2, authToken, battery, originalSettings.toBuilder()
						.setChargeToStateOfCharge( ChargeToStateOfCharge.newBuilder()
								.setSocPercentage( DoubleValue.of( 90d ) )
								.setChargePowerKwatts( DoubleValue.of( 4d ) )
								).build() );
				Thread.sleep( 1000 );
				
				logOutput( "Set battery to discharge to 30 percent" );
				changeBatteryToSettings( blockingStubV2, authToken, battery, originalSettings.toBuilder()
						.setDischargeToStateOfCharge( DischargeToStateOfCharge.newBuilder()
								.setSocPercentage( DoubleValue.of( 30d ) )
								.setDischargePowerKwatts( DoubleValue.of( 3d ) )
								).build() );
				Thread.sleep( 1000 );
				
				logOutput( "Set battery to idle" );
				changeBatteryToSettings( blockingStubV2, authToken, battery, originalSettings.toBuilder()
						.setIdle( Idle.getDefaultInstance() )
						.build() );
				Thread.sleep( 1000 );
				
				logOutput( "cause an error by trying to set the discharge power higher than the battery's inverter supports" );
				try
				{
					changeBatteryToSettings( blockingStubV2, authToken, battery, originalSettings.toBuilder()
							.setDischargeToStateOfCharge( DischargeToStateOfCharge.newBuilder()
									.setSocPercentage( DoubleValue.of( 30d ) )
									.setDischargePowerKwatts( DoubleValue.of( 100d ) )
									).build() );
				}
				catch(StatusRuntimeException invalidArgument)
				{
					logOutput( "Caught the expected exception: " + invalidArgument.getMessage() );
				}
				
				// now change it back to the original settings
				logOutput( "\n*** Setting the battery back to the original settings" );
				changeBatteryToSettings( blockingStubV2, authToken, battery, originalSettings );
			}
		}
		catch( StatusRuntimeException e )
		{
			e.printStackTrace();
			logOutput( "WARNING: RPC failed: %s", e.getMessage() );
			return;
		}
	}
	
	/** Set an EV Charger to the provided settings */
	private static void changeEVChargerToSettings(PartnerApiBlockingStub blockingStubV2, String authToken, Device evCharger, EVChargerSettings settings) throws InterruptedException
	{
		UpdateEVChargersRequest updateRequest = UpdateEVChargersRequest.newBuilder()
				.setAuthToken( authToken )
				.addSettings( settings )
				.build();
		
		EVChargersResponse updateResponse = blockingStubV2.updateEVChargers( updateRequest );
		if( updateResponse.getEvchargersCount() == 1  )		// will return us the device if it was changed to the new setting
		{
			EVCharger updatedEVSE = updateResponse.getEvchargers(0);
			logOutput( "Changed %s's to %s", evCharger.getManufacturerDeviceId(), updatedEVSE.getSettings() ); 
		}
		else
			logOutput("ERROR: failed to update: %s", updateResponse);
	}

	/** Set a  battery to the provided settings */
	private static void changeBatteryToSettings(PartnerApiBlockingStub blockingStubV2, String authToken, Device battery, BatterySettings settings) throws InterruptedException
	{
		UpdateBatteriesRequest updateRequest = UpdateBatteriesRequest.newBuilder()
				.setAuthToken( authToken )
				.addSettings( settings )
				.build();
		
		BatteriesResponse updateResponse = blockingStubV2.updateBatteries( updateRequest );
		if( updateResponse.getBatteriesCount() == 1  )		// will return us the device if it was changed to the new setting
		{
			Battery updatedBattery = updateResponse.getBatteries(0);
			logOutput( "Changed %s's to %s", battery.getManufacturerDeviceId(), updatedBattery.getSettings() ); 
		}
		else
			logOutput("ERROR: failed to update: %s", updateResponse);
	}

	/** format the output and print it to the console */
	static private void logOutput(String logLineWithPlaceholders, Object... logLineArguments)
	{
		System.out.println( String.format(logLineWithPlaceholders, logLineArguments) );
	}
}
