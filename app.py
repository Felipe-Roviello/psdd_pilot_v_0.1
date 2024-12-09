""" 
Combining all features we will need, including dinamic dropdown menus. 
"""
from pathlib import Path 
from shiny import ui, render, App, Inputs, Outputs, Session, reactive 
import pandas as pd 
import plotly.express as px 
#import textwrap 
from datetime import date 
from shinywidgets import output_widget, render_widget  

# Define o UI
app_ui = ui.page_fluid(
    ui.layout_sidebar(
        ui.sidebar(
            ui.output_ui("update_dropdown")
        ),#sidebar 
        
        ui.navset_tab(
            ui.nav_panel(
                ui.panel_title("Table"), 
                ui.card(ui.output_data_frame("summary_table")), 
                ui.download_button("download", "Download data"), 
                value = "table_tab",
            ), 
            
            ui.nav_panel(
                ui.panel_title("Chart"), 
                ui.card(output_widget("chart")), 
                value = "chart_tab",
            ), 

            ui.nav_panel(
                ui.panel_title("Report"), 

                ui.output_ui("main_c_selection"), 

                ui.output_ui("report_ui"), 

                ui.card(ui.card_header('Evolution of productivity and fixed assets'), output_widget("report_chart1")), 
                ui.card(ui.output_text("report_text1", inline = True)),  

                ui.card(ui.card_header('Decomposition of productivity'), output_widget("report_chart2")), 
                ui.card(ui.output_text("report_text2", inline = True)), 

                value = "report_tab",
            ), 

            id = "active_tab" 
        )#navset_tab 
    )#layout_sidebar 
)#page_fluid 

#Global used to keep track of the selected items in the sidebar 
first_iteration = True 
first_choice = True 

def server(input: Inputs, output: Outputs, session: Session):
    
    infile = Path(__file__).parent / "PSDD_fake.csv" 
    df = pd.read_csv(infile) 
    #df = pd.read_stata(r"C:\Users\Felipe\Documents\WorldBank\Nicolo\psdd\newCode\run_code\output\PSDD_fake.dta")  
    #df = pd.read_stata(r"C:\Users\Felipe\Documents\WorldBank\Nicolo\psdd\newCode\run_code\output\PSDD.dta")  
    #df = pd.read_stata(r'C:\Users\Felipe\Documents\WorldBank\Nicolo\psdd\newCode\data_test\psdd_full_2.dta') 
    df['year'] = df['year'].astype(int).astype(str) 

    print('DATA OPENED') 

    #Lists of variables to choose from 
    country_lst = list(df['country'].unique()) 
    year_lst = list(df['year'].unique()) 
    measure_lst = list(df['measure'].unique()) 
    macro_lst = list(df['macrosector'].unique()) 
    weighted_lst = list(df['weighted'].unique()) 
    group_lst = list(df['group'].unique()) 
    ln_lst = list(df['is_ln'].unique()) 
    currency_lst = list(df['currency'].unique()) 

    #Dictionary to use as the list of available variables 
    global var_dic 
    df['descr2'] = df['descr'] 
    var_dic = (df.set_index('descr').groupby('to_dic')['descr2']
            .agg(lambda g: g.to_dict())
            .to_dict()
        ) 
    
    #Dictionary of countries  
    df['country2'] = df['country'] 
    global cntry_dic 
    cntry_dic = (df.set_index('country').groupby('region')['country2']
            .agg(lambda g: g.to_dict())
            .to_dict()
        ) 
    
    #Shorter df with vars 
    df_vars = df.groupby(['country', 'descr', 'measure', 'macrosector', 'weighted', 'group', 'is_ln', 'descr2', 'to_dic'])[['value']].mean().reset_index() 
    df_vars = df_vars.drop(columns = ['value']) 

    def report_filter(): 
        try: 
            main_country = input.main_c_drop() 
            peers = list(input.country_drop())
        except: 
            main_country = '' 
            peers = [] 
        
        def get_main(x): 
            if x == main_country: 
                return main_country 
            else: 
                return 'Peer average' 
    
        df_ = df.copy() 
        #List of countries 
        _cntryLst = list(input.country_drop()) 
        _cntryLst.append(input.main_c_drop()) 
        print('list of countries:', _cntryLst)
        df_ = df_[df_['country'].isin(_cntryLst)] 
        df_ = df_[df_['year'].isin([str(y) for y in list(range(int(input.year_drop()[0]), int(input.year_drop()[1] + 1)))])] 

        df_ = df_[df_['level'].isin(['country-year'])] 
        #FILTER FOR CURRENT USD 
        df_ = df_[df_['currency'].isin(['USD'])] 

        #For decomposition 
        df_rep2 = df_[df_['variable'].isin(['opcs_between_ln_lp_va', 'opcs_total_ln_lp_va', 'opcs_within_ln_lp_va'])] 
        df_rep2 = df_rep2[df_rep2['country'] == input.main_c_drop()] 
        df_rep2['first_val'] = df_rep2.groupby('descr')['value'].transform('first')
        df_rep2['val_to_first'] = df_rep2['value'] - df_rep2['first_val'] 
        #df_rep2['val_to_first'] = df_rep2['value'] 

        df_rep2 = df_rep2.sort_values(by = ['year']) 
        df_rep2['descr'] = df_rep2['descr'].str.replace('Labor productivity - ', '', regex = True)  
        df_rep2['descr'] = df_rep2['descr'].str[:-20] 

        print('Main country decomp:', df_rep2['country'].unique())

        #Continue
        df_ = df_[df_['weighted'].isin(['Unweighted'])] 
        df_ = df_[df_['variable'].isin(['lp_va', 'ae'])] 
        
        df_['main'] = df_['country'].apply(lambda x: get_main(x)) 

        df_peer = df_[df_['main'] == 'Peer average'] 
        df_m = df_peer.groupby(['main', 'year', 'descr'])[['value']].mean().reset_index() 
        df_m = df_m.rename(columns = {'main': 'country'}) 

        df_rep1 = pd.concat([df_, df_m])
        df_rep1 = df_rep1[['country', 'year', 'descr', 'value']] 
        df_rep1 = df_rep1.sort_values(by = ['year']) 

        return (df_rep1, df_rep2)  

    @output 
    @render_widget 
    def report_chart1(): 
        #global dfr0 
        #global dfr1 
        #dfrl = report_filter() 
        #dfr0 = dfrl[0] 
        #dfr1 = dfrl[1] 

        try: 
            _main = input.main_c_drop() 
        except: 
            _main = '' 
            
        #Legend parameters 
        labs = {'country': 'Country', 'group_descr': 'Group description', 'descr': 'Variable', 'group': 'Group', 'value': 'Value', 
                'year': 'Year', 'macrosector': 'Sector'}  

        df = report_filter()[0] 
        
        fig = px.line(df, x = "year", y = "value", color = 'country', symbol = 'descr', labels = labs, 
                      title = 'Main country: {}'.format(_main))   

        fig.update_layout(legend=dict(font=dict(size= 10))) 
        return fig 
    
    @output 
    @render_widget 
    def report_chart2(): 
        try: 
            _main = input.main_c_drop() 
            df = report_filter()[1] 

            print('country in chart 2:', df['country'].unique()) 
            #Legend parameters 
            labs = {'country': 'Country', 'group_descr': 'Group description', 'descr': 'Variable', 'group': 'Group', 'value': 'Value', 
                    'year': 'Year', 'macrosector': 'Sector', 'val_to_first': 'Value'}  
            
            #df = report_filter()[1] 
            
            fig = px.line(df, x = "year", y = "val_to_first", color = 'descr', labels = labs, 
                        title = 'Olley-Pakes decomposition of labor productivity - {}'.format(_main))   

            fig.update_layout(legend=dict(font=dict(size= 10))) 
            return fig 
        except: 
            pass
    
    @output
    @render.text 
    def report_text1(): 
        
        try: 
            _main = input.main_c_drop() 
            #df = report_filter()[0] 
            df = report_filter()[0] 

            #growth main 
            df_m = df[df['country'] == _main] 

            df_m_ae = df_m[df_m['descr'] == 'Average of assets/employment'] 
            ae_m = df_m_ae['value'].iloc[-1] 
            g_m_ae = 100*(df_m_ae['value'].iloc[-1] - df_m_ae['value'].iloc[0])/df_m_ae['value'].iloc[0] 
            g_m_ae_str = str(round(g_m_ae, 2)) 

            df_m_lp = df_m[df_m['descr'] == 'Average of va/employment'] 
            lp_m = df_m_lp['value'].iloc[-1] 
            g_m_lp = 100*(df_m_lp['value'].iloc[-1] - df_m_lp['value'].iloc[0])/df_m_lp['value'].iloc[0] 
            g_m_lp_str = str(round(g_m_lp, 2)) 

            #Growth peers 
            df_p = df[df['country'] == 'Peer average'] 

            df_p_ae = df_p[df_p['descr'] == 'Average of assets/employment'] 
            ae_p = df_p_ae['value'].iloc[-1] 
            g_p_ae = 100*(df_p_ae['value'].iloc[-1] - df_p_ae['value'].iloc[0])/df_p_ae['value'].iloc[0] 
            g_p_ae_str = str(round(g_p_ae, 2)) 

            df_p_lp = df_p[df_p['descr'] == 'Average of va/employment'] 
            lp_p = df_p_lp['value'].iloc[-1] 
            g_p_lp = 100*(df_p_lp['value'].iloc[-1] - df_p_lp['value'].iloc[0])/df_p_lp['value'].iloc[0] 
            g_p_lp_str = str(round(g_p_lp, 2)) 

            if ae_m > ae_p: 
                ae_ind = 'higher' 
            else: 
                ae_ind = 'lower' 
            
            if lp_m > lp_p: 
                lp_ind = 'higher' 
            else: 
                lp_ind = 'lower' 
            
            if lp_ind != ae_ind: 
                ind_connector = 'On the other hand' 
            else: 
                ind_connector = 'Similarly'  
            
            if g_m_ae > 0: 
                connector_m_ae = 'increased' 
            else: 
                connector_m_ae = 'decreased' 

            if g_m_lp > 0: 
                connector_m_lp = 'increased' 
            else: 
                connector_m_lp = 'decreased' 

            if g_p_ae > 0: 
                connector_p_ae = 'increased' 
            else: 
                connector_p_ae = 'decreased' 

            txt = """In the latest year available, labor productivity in {main_c} was {_lp_ind} than the average of its peers. 
                {_ind_connector}, the ratio of assets over employment was {_ae_ind} than comparators. 
                During the selected period, labor productivity in {main_c} {_connector_m_lp} by {_g_m_lp_str} percent.
                Furthermore, assets over employment {_connector_m_ae} by {_g_m_ae_str} percent.
                In the same timeframe, the average labor productivity growth in peer countries was of {_g_p_lp_str} percent,
                while assets over employment {_connector_p_ae} by {_g_p_ae_str} percent. The chart above shows monetary values 
                in constant 2019 LCU converted to USD using real exchange rates.""".format(main_c = _main, 
                _lp_ind = lp_ind, _ind_connector = ind_connector, _ae_ind = ae_ind,                                                                                  
                _connector_m_lp = connector_m_lp, _g_m_lp_str = g_m_lp_str, 
                _connector_m_ae = connector_m_ae, _g_m_ae_str = g_m_ae_str, _g_p_lp_str = g_p_lp_str, 
                _connector_p_ae = connector_p_ae, _g_p_ae_str = g_p_ae_str) 

            return txt 
        except: 
            return 'Please select a main country and peers'  
    
    @output
    @render.text 
    def report_text2(): 
        try: 
            _main = input.main_c_drop() 
            #df = report_filter()[1] 
            df = report_filter()[1] 

            #Main driver of growth 
            last_years = df.loc[df.groupby('variable')['year'].idxmax()]
            # Create the dictionary
            result_dict = dict(zip(last_years['variable'], last_years['val_to_first']))

            if result_dict['opcs_total_ln_lp_va'] > 0: 
                agg = 'growth' 
            else: 
                agg = 'decline'

            if result_dict['opcs_between_ln_lp_va'] > result_dict['opcs_within_ln_lp_va']: 
                main_driver = 'between' 
            else: 
                main_driver = 'within' 
                           
            txt = """The chart above shows the Olley-Pakes decomposition of labor productivity (cumulative sum) 
            for {main_c} relative to the first year. The total component measures labor productivity. The within 
            component represents the productivity of the average firm in the economy, while the between component is a measure 
            of allocative efficiency. If firms that are productive end up being larger in an economy, a positive 
            relationship between size and productivity should emerge, and the between component will be positive.
            In the selected period, the {_agg} in aggregate productivity was mainly driven by the {_main_driver} 
            component.""".format(main_c = _main, 
            _agg = agg, _main_driver = main_driver)  

            return txt 
        except: 
            return 'Please select a main country and peers'  

    @reactive.Calc 
    def _filter_data(): 

        #global country_selected 
        #print('Countries inside filterdata 1:', country_selected)  

        #Look at reactive.effect to see why we are doing this 
        global react_var_drop 
        react_var_drop = reactive.value(input.var_drop()) 

        df_ = df.copy() 
        df_ = df_[df_['descr'].isin(react_var_drop.get())] 

        df_ = df_[df_['country'].isin(input.country_drop())] 
        df_ = df_[df_['measure'] == input.measure_drop()] 
        df_ = df_[df_['currency'] == input.currency_drop()] 
        df_ = df_[df_['group'] == input.group_drop()] 
        df_ = df_[df_['macrosector'].isin(input.macro_drop())] 
        df_ = df_[df_['weighted'] == input.weighted_drop()] 
        df_ = df_[df_['is_ln'] == input.ln_drop()] 
        df_ = df_[df_['year'].isin([str(y) for y in list(range(int(input.year_drop()[0]), int(input.year_drop()[1] + 1)))])] 

        df_ = df_.sort_values(by = ['year']) 


        return df_ 

    @output 
    @render.data_frame 
    def summary_table(): 
        df = _filter_data() 
        df = df.drop(columns = ['is_decomposition', 'to_dic', 'measure', 'variable', 'block', 
                                'descr2', 'country2', 'not_stata_0', 'source', 'size_coverage', 
                                'geo_coverage', 'legal_form', 'is_ln', 'currency', 'WBcode', 'level']) 
        df.columns = [col.capitalize() for col in df.columns] 
        return df  
    
    def _size_sorter(column):
        """Sort function for group size"""
        teams = ['[0-4]',  '(4-9]', '(9-19]', '(19-49]', '(49-99]', '(99-499]', '>499', 'No size info']
        correspondence = {team: order for order, team in enumerate(teams)}
        return column.map(correspondence) 
    
    def _age_sorter(column):
        """Sort function for group age"""
        teams = ["1-5", "6-10", "11-15", "15+", "No age info"]
        correspondence = {team: order for order, team in enumerate(teams)}
        return column.map(correspondence) 

    def _decile_sorter(column):
        """Sort function for group deciles"""
        teams = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'] 
        correspondence = {team: order for order, team in enumerate(teams)}
        return column.map(correspondence) 
    
    
    @output 
    @render_widget 
    def chart(): 
        df = _filter_data() 

        is_group = 0  
        try: #try is only important when initiating the dashboard, as there is no df. 
                if df['group'].unique()[0] != 'No group': 
                    is_group = 1 
        except: 
            pass 

        if is_group == 1: 
            #For the df if a group is chosen sort in the correct order. Order by year later
            group_type = df['group'].iloc[0] 
            if group_type == 'Size': 
                _order = {'group_descr': ['[0-4]',  '(4-9]', '(9-19]', '(19-49]', '(49-99]', '(99-499]', '>499', 'No size info']}
            elif group_type == 'Age': 
                _order = {'group_descr': ["1-5", "6-10", "11-15", "15+", "No age info"]} 
            elif group_type in ['LP decile', 'TFPR decile', 'MKP decile']: 
                _order = {'group_descr': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']} 

        #nunq_cntry = df['country'].nunique() 
        nunq_vars = df['descr'].nunique() 
        #unq_cntry = df['country'].unique() 
        unq_vars = df['descr'].unique() 
        nunq_sec = df['macrosector'].nunique() 

        #Legend parameters 
        labs = {'country': 'Country', 'group_descr': 'Group description', 'descr': 'Variable', 'group': 'Group', 'value': 'Value', 
                'year': 'Year', 'macrosector': 'Sector'}  

        #def customwrap(s,width=20):
        #    return "<br>".join(textwrap.wrap(s,width=width)) 
        
        def onlycountries(x): 
            if x['text'].split("=")[-1] in country_lst: 
                return True 
            else: 
                return False 

        if input.chart_drop() == 'Line': #Line 
            #If the variable has a group, plot the evolution of the variable in each group 

            if is_group == 1: #Can have multiple charts - change simble to country and color to group_descr 

                if nunq_vars > 1 and nunq_sec == 1: #If the user picks more than one variable split the charts in two 
                    fig = px.line(df, x = "year", y = "value", color = 'group_descr', symbol = 'descr', facet_row = 'country', 
                                  labels = labs)  
                    fig.update_yaxes(matches = None) 
                    #fig.for_each_annotation(lambda a: a.update(text=customwrap(a.text.split("=")[-1])), selector = onlycountries) 
                    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]), selector = onlycountries) 
                    fig.update_annotations(font_size=10) 

                elif nunq_vars >= 1 and nunq_sec > 1: #If the user picks more than one variable and more than one sector, further split 
                    fig = px.line(df, x = "year", y = "value", color = 'group_descr', symbol = 'macrosector', facet_row = 'country', 
                                  facet_col = 'descr', labels = labs)  
                    fig.update_yaxes(matches = None) 
                    #fig.for_each_annotation(lambda a: a.update(text=customwrap(a.text.split("=")[-1])), selector = onlycountries) 
                    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]), selector = onlycountries) 
                    fig.update_annotations(font_size=10) 

                else: #Else, keep only one chart 
                    fig = px.line(df, x = "year", y = "value", color = 'group_descr', symbol = 'country', labels = labs) 

            else: #Only one chart 
                if nunq_vars > 1 and nunq_sec == 1: 
                    print("A") 
                    fig = px.line(df, x = "year", y = "value", color = 'country', symbol = 'descr', 
                    labels = labs)  

                elif nunq_sec > 1 and nunq_vars == 1: 
                    print("B") 
                    fig = px.line(df, x = "year", y = "value", color = 'country', symbol = 'macrosector', 
                    labels = labs)  
                
                elif nunq_sec > 1 and nunq_vars > 1: 
                    print("C") 
                    fig = px.line(df, x = "year", y = "value", color = 'macrosector', symbol = 'descr', facet_row = 'country', 
                    labels = labs)  
                    fig.update_yaxes(matches = None) 
                    #fig.for_each_annotation(lambda a: a.update(text=customwrap(a.text.split("=")[-1])), selector = onlycountries) 
                    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]), selector = onlycountries) 
                    fig.update_annotations(font_size=10) 

                else: 
                    print("D") 
                    fig = px.line(df, x = "year", y = "value", color = 'country', symbol = 'descr', 
                    labels = labs) 

        else: #Bar 
            if is_group == 1: #With groups 
                print('Number of vars:', nunq_vars) 
                print('Number of sectors:', nunq_sec) 
                if nunq_vars > 1 and nunq_sec == 1: 
                    print("A") 
                    fig = px.bar(df, x = "group_descr", y = "value", color = 'descr', barmode = 'group', facet_row = 'country', 
                                  labels = labs, category_orders = _order) 
                    fig.update_yaxes(matches = None) 
                    #fig.for_each_annotation(lambda a: a.update(text=customwrap(a.text.split("=")[-1])), selector = onlycountries) 
                    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]), selector = onlycountries) 
                    fig.update_annotations(font_size=10) 
                
                elif nunq_vars == 1 and nunq_sec > 1: 
                    print("B") 
                    fig = px.bar(df, x = "group_descr", y = "value", color = 'macrosector', barmode = 'group', facet_row = 'country', 
                                  labels = labs, category_orders = _order) 
                    fig.update_yaxes(matches = None) 
                    #fig.for_each_annotation(lambda a: a.update(text=customwrap(a.text.split("=")[-1])), selector = onlycountries) 
                    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]), selector = onlycountries) 
                    fig.update_annotations(font_size=10) 
                
                elif nunq_vars > 1 and nunq_sec > 1: 
                    print("C") 
                    fig = px.bar(df, x = "group_descr", y = "value", color = 'macrosector', barmode = 'group', facet_row = 'country', 
                                  facet_col = "descr", labels = labs, category_orders = _order) 
                    fig.update_yaxes(matches = None) 
                    #fig.for_each_annotation(lambda a: a.update(text=customwrap(a.text.split("=")[-1])), selector = onlycountries) 
                    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]), selector = onlycountries) 
                    fig.update_annotations(font_size=10) 

                else: 
                    print("D") 
                    fig = px.bar(df, x = "group_descr", y = "value", color = 'country', barmode = 'group', labels = labs, 
                                 category_orders = _order) 
            
            else: #No groups 
                if nunq_vars > 1 and nunq_sec == 1:  
                    #print("A") 
                    fig = px.bar(df, x = "year", y = "value", color = 'descr', barmode = 'group', facet_row = 'country', 
                                  labels = labs) 
                    fig.update_yaxes(matches = None) 
                    #fig.for_each_annotation(lambda a: a.update(text=customwrap(a.text.split("=")[-1])), selector = onlycountries) 
                    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]), selector = onlycountries) 
                    fig.update_annotations(font_size=10) 
                
                elif nunq_vars == 1 and nunq_sec > 1:  
                    #print("B") 
                    fig = px.bar(df, x = "year", y = "value", color = 'macrosector', barmode = 'group', facet_row = 'country', 
                                 labels = labs)  

                elif nunq_vars > 1 and nunq_sec > 1:  
                    #print("C") 
                    fig = px.bar(df, x = "year", y = "value", color = 'macrosector', barmode = 'group', facet_row = 'country', 
                                 facet_col = 'descr', labels = labs) 
                    fig.update_yaxes(matches = None) 
                    #fig.for_each_annotation(lambda a: a.update(text=customwrap(a.text.split("=")[-1])), selector = onlycountries) 
                    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]), selector = onlycountries) 
                    fig.update_annotations(font_size=10) 

                else: 
                    #print("D") 
                    fig = px.bar(df, x = "year", y = "value", color = 'country', barmode = 'group', labels = labs)  

        #Legend
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="right", x=1)) 
        return fig 

    global main_c_track 
    main_c_track = False 
    @render.ui 
    @reactive.event(input.active_tab) 
    def main_c_selection(): 
        global main_c_selected 
        global main_c_track 

        if main_c_track == False: 
            main_c_selected = None 
            main_c_track = True 
        else: 
            main_c_selected = input.main_c_drop() 
            
        return ui.input_selectize("main_c_drop", "Select the main country. Peers can be selected on the selection box in the top-left corner", 
                                  choices = cntry_dic, selected = main_c_selected, width = '900px')  
    

    @render.ui 
    @reactive.event(input.active_tab) 
    def update_dropdown(): 
        #Get the active tab 
        current_tab = str(input['active_tab']()) 
        #print("Current tab:", str(input['active_tab']())) 

        #To ensure that the selection remains the same when the tab is changed, access the global variable. 
        #If 0 (first interaction) set a default value and set the value to something different than 0. 
        #If not 0, use the previous input. 
        global first_iteration 
        global var_dic  
        global cntry_dic 
        
        global country_selected 
        global year_selected 
        global measure_selected
        global ln_selected 
        global macro_selected 
        global weighted_selected 
        global group_selected 
        global var_selected 
        global chart_selected 
        global currency_selected 
        
        #print('First iteration', first_iteration) 
        if first_iteration == True: 
            
            country_selected = [] 
            year_selected = [min([int(y) for y in year_lst]), max([int(y) for y in year_lst])] 
            measure_selected = None  
            macro_selected =  None
            weighted_selected = None
            ln_selected = None 
            group_selected = None
            var_selected = [] 
            chart_selected = 'Line' 
            currency_selected = None 

            first_iteration = False 
        else: 
            measure_selected = input.measure_drop() 
            weighted_selected = input.weighted_drop() 
            ln_selected = input.ln_drop() 
            group_selected = input.group_drop() 

            macro_selected = list(input.macro_drop()) 
            var_selected = list(input.var_drop()) 
            year_selected = list(input.year_drop()) 

            chart_selected = input.chart_drop() 
            currency_selected = input.currency_drop() 


            country_selected = list(input.country_drop())  
            #print('Countries inside update_dropdown 1:', country_selected) 
           
        #Dinamic sidebar: add all menus needed here 
        if current_tab == "table_tab": 
            #print("In tab:", current_tab) 
            return (
                ui.input_selectize("country_drop", "Country", choices = cntry_dic, selected = country_selected, multiple = True),  
                #Replace by input_slider 
                #ui.input_selectize("year_drop", "Year", choices = year_lst, selected = year_selected, multiple = True),    
                ui.input_slider("year_drop", "Year", min = min([int(y) for y in year_lst]), max = max([int(y) for y in year_lst]), value=year_selected, sep = ''), 

                ui.input_selectize("measure_drop", "Measure", choices = measure_lst, selected = measure_selected),    

                ui.input_selectize("currency_drop", "Currency", choices = currency_lst, selected = currency_selected),    

                ui.input_selectize("macro_drop", "Sector", choices = macro_lst, selected = macro_selected, multiple = True), 

                ui.input_selectize("weighted_drop", "Weight/decomposition", choices = weighted_lst, selected = weighted_selected),      
                
                ui.input_selectize("ln_drop", "Level or log", choices = ln_lst, selected = ln_selected), 

                ui.input_selectize("group_drop", "Group", choices = group_lst, selected = group_selected),  

                ui.input_selectize("var_drop", "Variable", choices = var_dic, selected = var_selected, multiple = True),  

                ui.input_selectize("chart_drop", ui.HTML("<span style='color: #aaa'>Chart type</span>"), 
                                   choices = ['Line', 'Bar'], selected = chart_selected, 
                                   options=({
                    #Disabling option and changing color of the options to grey 
                    "render": ui.js_eval( 
                        '{option: function(item, escape) {return "<div style = color:#aaa;pointer-events:none>"  + escape(item.label) + "</div>";}}'                              
                        ), 
                    })
                ),#input_selectize 
                #This controls the inside of the dropdown menu for chart_drop. input:after is the arrow 
                ui.tags.style(ui.HTML("""
                #chart_drop ~ .selectize-control.single .selectize-input {border: 1px solid #aaa; background-color: #f0f0f0; color: #aaa;}
                #chart_drop ~ .selectize-control.single .selectize-input:after {visibility:hidden;}
                """)),   
            )#return 
        
        elif current_tab == "chart_tab": 
            #print("In tab:", current_tab) 
            return ( 
                ui.input_selectize("country_drop", "Country", choices = cntry_dic, selected = country_selected, multiple = True), 

                ui.input_slider("year_drop", "Year", min = min([int(y) for y in year_lst]), max = max([int(y) for y in year_lst]), value=year_selected, sep = ''), 

                ui.input_selectize("measure_drop", "Measure", choices = measure_lst, selected = measure_selected), 

                ui.input_selectize("currency_drop", "Currency", choices = currency_lst, selected = currency_selected),   

                ui.input_selectize("macro_drop", "Sector", choices = macro_lst, selected = macro_selected, multiple = True), 

                ui.input_selectize("weighted_drop", "Weight/decomposition", choices = weighted_lst, selected = weighted_selected),  

                ui.input_selectize("ln_drop", "Level or log", choices = ln_lst, selected = ln_selected), 

                ui.input_selectize("group_drop", "Group", choices = group_lst, selected = group_selected),    

                ui.input_selectize("var_drop", "Variable", choices = var_dic, selected = var_selected, multiple = True), 

                ui.input_selectize("chart_drop", "Chart type", choices = ['Line', 'Bar'], selected = chart_selected), 

            )#return 
        
        elif current_tab == "report_tab": 
            #print("In tab:", current_tab) 
            return ( 
                ui.input_selectize("country_drop", "Country", choices = cntry_dic, selected = country_selected, multiple = True), 

                ui.input_slider("year_drop", "Year", min = min([int(y) for y in year_lst]), max = max([int(y) for y in year_lst]), value=year_selected, sep = ''), 

                ui.input_selectize("measure_drop", ui.HTML("<span style='color: #aaa'>Measure</span>"), 
                                   choices = measure_lst, selected = measure_selected, 
                                   options=({
                    #Disabling option and changing color of the options to grey 
                    "render": ui.js_eval( 
                        '{option: function(item, escape) {return "<div style = color:#aaa;pointer-events:none>"  + escape(item.label) + "</div>";}}'                              
                        ), 
                    })
                ),#input_selectize 
                #This controls the inside of the dropdown menu for chart_drop. input:after is the arrow 
                ui.tags.style(ui.HTML("""
                #measure_drop ~ .selectize-control.single .selectize-input {border: 1px solid #aaa; background-color: #f0f0f0; color: #aaa;}
                #measure_drop ~ .selectize-control.single .selectize-input:after {visibility:hidden;}
                """)),   

                ui.input_selectize("currency_drop", ui.HTML("<span style='color: #aaa'>Currency</span>"), 
                                   choices = currency_lst, selected = currency_selected, 
                                   options=({
                    #Disabling option and changing color of the options to grey 
                    "render": ui.js_eval( 
                        '{option: function(item, escape) {return "<div style = color:#aaa;pointer-events:none>"  + escape(item.label) + "</div>";}}'                              
                        ), 
                    })
                ),#input_selectize 
                #This controls the inside of the dropdown menu for chart_drop. input:after is the arrow 
                ui.tags.style(ui.HTML("""
                #currency_drop ~ .selectize-control.single .selectize-input {border: 1px solid #aaa; background-color: #f0f0f0; color: #aaa;}
                #currency_drop ~ .selectize-control.single .selectize-input:after {visibility:hidden;}
                """)),   

                ui.input_selectize("macro_drop", ui.HTML("<span style='color: #aaa'>Sector</span>"), 
                                   choices = macro_lst, selected = macro_selected, multiple = True, 
                                   options=({
                    #Disabling option and changing color of the options to grey 
                    "render": ui.js_eval( 
                        '{option: function(item, escape) {return "<div style = color:#aaa;pointer-events:none>"  + escape(item.label) + "</div>";}}'                              
                        ), 
                    })
                ),#input_selectize 
                #This controls the inside of the dropdown menu for chart_drop. input:after is the arrow 
                ui.tags.style(ui.HTML("""
                #macro_drop ~ .selectize-control.single .selectize-input {border: 1px solid #aaa; background-color: #f0f0f0; color: #aaa;}
                #macro_drop ~ .selectize-control.single .selectize-input:after {visibility:hidden;}
                """)),   

                ui.input_selectize("weighted_drop", ui.HTML("<span style='color: #aaa'>Weight/decomposition</span>"), 
                                   choices = weighted_lst, selected = weighted_selected, 
                                   options=({
                    #Disabling option and changing color of the options to grey 
                    "render": ui.js_eval( 
                        '{option: function(item, escape) {return "<div style = color:#aaa;pointer-events:none>"  + escape(item.label) + "</div>";}}'                              
                        ), 
                    })
                ),#input_selectize 
                #This controls the inside of the dropdown menu for chart_drop. input:after is the arrow 
                ui.tags.style(ui.HTML("""
                #weighted_drop ~ .selectize-control.single .selectize-input {border: 1px solid #aaa; background-color: #f0f0f0; color: #aaa;}
                #weighted_drop ~ .selectize-control.single .selectize-input:after {visibility:hidden;}
                """)),   

                ui.input_selectize("ln_drop", ui.HTML("<span style='color: #aaa'>Level or log</span>"), 
                                   choices = ln_lst, selected = ln_selected, 
                                   options=({
                    #Disabling option and changing color of the options to grey 
                    "render": ui.js_eval( 
                        '{option: function(item, escape) {return "<div style = color:#aaa;pointer-events:none>"  + escape(item.label) + "</div>";}}'                              
                        ), 
                    })
                ),#input_selectize 
                #This controls the inside of the dropdown menu for chart_drop. input:after is the arrow 
                ui.tags.style(ui.HTML("""
                #ln_drop ~ .selectize-control.single .selectize-input {border: 1px solid #aaa; background-color: #f0f0f0; color: #aaa;}
                #ln_drop ~ .selectize-control.single .selectize-input:after {visibility:hidden;}
                """)),   

                ui.input_selectize("group_drop", ui.HTML("<span style='color: #aaa'>Group</span>"), 
                                   choices = group_lst, selected = group_selected, 
                                   options=({
                    #Disabling option and changing color of the options to grey 
                    "render": ui.js_eval( 
                        '{option: function(item, escape) {return "<div style = color:#aaa;pointer-events:none>"  + escape(item.label) + "</div>";}}'                              
                        ), 
                    })
                ),#input_selectize 
                #This controls the inside of the dropdown menu for chart_drop. input:after is the arrow 
                ui.tags.style(ui.HTML("""
                #group_drop ~ .selectize-control.single .selectize-input {border: 1px solid #aaa; background-color: #f0f0f0; color: #aaa;}
                #group_drop ~ .selectize-control.single .selectize-input:after {visibility:hidden;}
                """)),   

                ui.input_selectize("var_drop", ui.HTML("<span style='color: #aaa'>Variable</span>"), 
                                   choices = var_dic, selected = var_selected, multiple = True, 
                                   options=({
                    #Disabling option and changing color of the options to grey 
                    "render": ui.js_eval( 
                        '{option: function(item, escape) {return "<div style = color:#aaa;pointer-events:none>"  + escape(item.label) + "</div>";}}'                              
                        ), 
                    })
                ),#input_selectize 
                #This controls the inside of the dropdown menu for chart_drop. input:after is the arrow 
                ui.tags.style(ui.HTML("""
                #var_drop ~ .selectize-control.single .selectize-input {border: 1px solid #aaa; background-color: #f0f0f0; color: #aaa;}
                #var_drop ~ .selectize-control.single .selectize-input:after {visibility:hidden;}
                """)),   

                ui.input_selectize("chart_drop", ui.HTML("<span style='color: #aaa'>Chart type</span>"), 
                                   choices = ['Line', 'Bar'], selected = chart_selected, 
                                   options=({
                    #Disabling option and changing color of the options to grey 
                    "render": ui.js_eval( 
                        '{option: function(item, escape) {return "<div style = color:#aaa;pointer-events:none>"  + escape(item.label) + "</div>";}}'                              
                        ), 
                    })
                ),#input_selectize 
                #This controls the inside of the dropdown menu for chart_drop. input:after is the arrow 
                ui.tags.style(ui.HTML("""
                #chart_drop ~ .selectize-control.single .selectize-input {border: 1px solid #aaa; background-color: #f0f0f0; color: #aaa;}
                #chart_drop ~ .selectize-control.single .selectize-input:after {visibility:hidden;}
                """)),   
            )#return 

    @render.download(filename=lambda: f"PSDD_data_{date.today().isoformat()}.csv")
    def download(): 
        df = _filter_data() 
        df = df.drop(columns = ['is_decomposition', 'to_dic', 'measure', 'variable', 'block', 
                                'descr2', 'country2', 'not_stata_0', 'source', 'size_coverage', 
                                'geo_coverage', 'legal_form']) 
        yield df.to_csv()
    

    #Update dropdown menus 
    @reactive.effect  
    #@reactive.event(input.var_drop) 
    def update_dropdown_varlist(): 
        global var_dic 
        global country_selected 
        
        #print('ON UPDATE VARLIST')
        #print('Countries inside reactive 1:', country_selected) 
        #print('Countries input inside reactive 1:', input.country_drop()) 

        df_ = df_vars.copy() 
        df_ = df_[df_['country'].isin(input.country_drop())] 
        #df_ = df_[df_['year'].isin([str(y) for y in list(range(int(input.year_drop()[0]), int(input.year_drop()[1] + 1)))])] 
        df_ = df_[df_['measure'] == input.measure_drop()] 
        #df_ = df_[df_['currency'] == input.currency_drop()]  
        df_ = df_[df_['macrosector'].isin(input.macro_drop())] 
        df_ = df_[df_['weighted'] == input.weighted_drop()] 
        df_ = df_[df_['group'] == input.group_drop()] 
        df_ = df_[df_['is_ln'] == input.ln_drop()] 
        
        #print('Countries inside reactive 2:', country_selected) 

        #Update list of available variables 
        var_dic = (df_.set_index('descr').groupby('to_dic')['descr2']
            .agg(lambda g: g.to_dict())
            .to_dict()
        ) 
        #Get the list of available variables for the conditions below 
        var_lst = list(df_['descr'].unique())  

        #react_var_drop contains the same info is input.var_drop(), but we can't call it here 
        #because it would trigger a reactive event creating the weird loop when quickly 
        #selecting variables. 
        if any(x in react_var_drop.get() for x in var_lst): 
            var_selected = react_var_drop.get() 
        else:  
            var_selected = [] 
 
        #Updating choices 
        if var_lst == []: 
            var_dic = ['No indicators available for the current selection'] 
        
        ui.update_selectize("var_drop", choices = var_dic, selected = var_selected, server = False) 

        #print('Countries inside reactive 3:', country_selected) 

# Cria o app
app = App(app_ui, server) 

""" 
PERECE QUE QUANDO MUDAMOS DE TAB A LISTA DE PAISES SELECIONADOS MUDA DE ORDEM, COM O ULTIMO PAIS SELECIONADO INDO PRA FRENTE. 
NA VERDADE ELE MUDA PARA A ORDER EM QUE OS PAISES APARECEM NO DICIONARIO DE PAISES
Parece que o problema acontece quando chamamos input.country_drop(). Ele reorganiza tudo em ordem alfabética. 
Contudo, isso ocorre quando mudamos de tab. Portanto precisamos preservar a order anterior ao mudarmos de tab. 
A ordem está em country_selected 

#######
O ERRO PARECE QUE ACONTECE QUANDO CLICAMOS VARIAS VEZES NO DROPDOWN DE VARIABLE, EM VARIAS VARIAVEIS MUITO RAPIDO. 
NAO PARECE ACONTECER QUANDO FAZEMOS DEVAGAR. 
ELE FICA OSCILANDO ENTRE AS SELEÇOES QUE FIZEMOS. 
TROCAR DE MEASURE PARECE RESOLVER 
ISSO PARECE QUE ACONTECE EM reactive.effect, talvez update_selectize tenha a ver 
Não é so um ciclo de 2 variaveis. Pode ser tbm com 3. Por exemplo, uma hora mosta lp, outra lp e tfpr e outra hora nada 

ACHO QUE O ERRO É em update_selectize, pois quando comentamos a linha dele e tentamos reproduzir o erro 
vemos que as coisas ainda passam por reactive.effect, mas não acontece o mesmo erro. 

THIS IS ON THE RIGHT TRACK, BUT STILL NEED ADJUSTMENTS. IT SEEMS TO GO BACK TO the first variable that was selected 
ALIAS, PARECE QUE ISSO AQUI NAO RODA QUANDO SELECIONAMOS AS VARIAVEIS, MAS RODA QUANDO SELECIONAMOS OUTROS PARAMETROS. 
QUNADO SELECTIONAMOS OUTROS PARAMETRO, ELE CONTINUA RODANDO REACTIVE EFFECT 2 VEZES. reac_var_selected NAO 
PAROU ISSO, MAS ESTÁ GUARDANDO A PRIMEIRA VARIAVEL QUE ESCOLHEMOS 
EU ACHO QUE ELE RODA 2 VEZES PQ ESTA FAZENDO IGUAL NA INICIALIZAÇÃO. 
ELE RODA DE NOVO reactive.effect PRA QQR input.algo() que colocamos aqui. Note que ele nao atualiza para year e currency. 
A IDEIA É FAZER DE TODOS os input.algo() REACTIVE VALUES!!! -> não funciona, pois não reage quando selectionamos um novo pais, por exemplo 
EU ACHO QUE SEI PQ ESTA RODANDO 2 VEZES: ELE RODA A PRIMEIRA VEZ PQ CHAMAMOS input() em reactive.effect e em _filter_data de novo. 

Funcionou: definir global react_var_drop em _filterData parece ajudar, pois podemos chamar global react_var_drop em reactve.effect sem chamar 
input. Mas agora quando mudamos de tab afeta choices e var_dic vira todas as variáveis. Para resolver isso bastou 
chamar var_dic como global em reactive.effect 
""" 