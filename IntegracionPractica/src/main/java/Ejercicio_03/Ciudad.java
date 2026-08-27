package Ejercicio_03;

public class Ciudad {
    private String nombre;
    private int cantidadHabitantes;
    private double imp1, imp2, imp3, imp4, imp5;
    private double gastoMantenimiento;

    public Ciudad(String nombre, int cantidadHabitantes, double imp1, double imp2, double imp3, double imp4, double imp5, double gastoMantenimiento) {
        this.nombre = nombre;
        this.cantidadHabitantes = cantidadHabitantes;
        this.imp1 = imp1;
        this.imp2 = imp2;
        this.imp3 = imp3;
        this.imp4 = imp4;
        this.imp5 = imp5;
        this.gastoMantenimiento = gastoMantenimiento;
    }

    public String getNombre() { return nombre; }

    public boolean esControlable() {
        return cantidadHabitantes > 100000;
    }

    public double calcularRecaudacion() {
        return imp1 + imp2 + imp3 + imp4 + imp5;
    }

    // Verifica si la ciudad está en deficit
    public boolean estaEnDeficit() {
        if (!esControlable()) {
            return false; // Verifica si la ciudad tiene mas de 100000 habitantes
        }
        return gastoMantenimiento > calcularRecaudacion();
    }

}
